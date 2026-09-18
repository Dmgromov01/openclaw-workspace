#!/usr/bin/env python3
"""Oura OAuth2 core (server-side flow): authorize, exchange, refresh, API v2.

Signatures verified against the LIVE Oura API on 2026-09-11:

    form-encoded body + valid client_id + wrong secret  -> 401 invalid_client
    extra / duplicated parameter (PKCE code_verifier,
        duplicated client_id)                           -> 400 invalid_request
    JSON body instead of form-encoded                   -> 400 "Bad Request"

Consequences encoded in this module:
  * POST bodies are application/x-www-form-urlencoded (never JSON);
  * exactly the documented parameters, nothing extra. Oura does NOT support
    PKCE, so code_verifier / code_challenge must never be sent;
  * exactly ONE client-auth mechanism: client_id/client_secret in the body
    (default), or HTTP Basic (fallback only, with the creds removed from body);
  * authorization codes and refresh tokens are single-use;
  * secrets are never printed or logged.
"""
from __future__ import annotations

import json
import os
import secrets
import sys
import time
import urllib.parse
from pathlib import Path
from typing import Any

import requests

AUTHORIZE_URL = "https://cloud.ouraring.com/oauth/authorize"
TOKEN_URL = "https://api.ouraring.com/oauth/token"
API_BASE = "https://api.ouraring.com/v2/usercollection"

WORKSPACE = Path(__file__).resolve().parents[1]
ENV_PATH = WORKSPACE / ".env"
STATE_PATH = WORKSPACE / ".oauth_state.json"

DEFAULT_REDIRECT_URI = "https://hub.gbkz.uk/"
# Full scope set, exactly as Oura itself expands it (observed live in the
# authorize redirect): email, personal, daily, heartrate, tag, workout, session,
# spo2Daily, ring_configuration, stress, heart_health.
# An EMPTY list is also valid: per the Oura docs, leaving scope blank makes the
# application request ALL available scopes - the most robust way to get everything.
DEFAULT_SCOPES = [
    "email", "personal", "daily", "heartrate", "tag", "workout", "session",
    "spo2Daily", "ring_configuration", "stress", "heart_health",
]

STATE_TTL_SECONDS = 600
REFRESH_SKEW_SECONDS = 120
HTTP_TIMEOUT = 30


class OuraOAuthError(RuntimeError):
    """Oura rejected the request. Carries an actionable diagnosis."""

    def __init__(self, status: int, code: str, description: str, diagnosis: str) -> None:
        self.status = status
        self.code = code
        self.description = description
        self.diagnosis = diagnosis
        super().__init__(diagnosis)


# --------------------------------------------------------------------------- #
# .env store (0600). Same keys the existing project already uses.
# --------------------------------------------------------------------------- #

def read_env(path: Path = ENV_PATH) -> dict[str, str]:
    values: dict[str, str] = {}
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            values[key.strip()] = value.strip().strip('"')
    return values


def write_env(values: dict[str, str], path: Path = ENV_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = ['{0}="{1}"'.format(k, v) for k, v in values.items()]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    os.chmod(path, 0o600)


# --------------------------------------------------------------------------- #
# Error parsing + actionable diagnosis
# --------------------------------------------------------------------------- #

def parse_error(status: int, text: str) -> tuple[str, str]:
    """Return (error_code, description) for an Oura error response."""
    try:
        data = json.loads(text)
    except Exception:
        return "unknown_error", text[:200]
    if isinstance(data, dict):
        code = str(data.get("error") or data.get("error_code") or "")
        desc = str(data.get("error_description") or data.get("title") or "")
        if not code:
            code = "malformed_request" if data.get("title") else "unknown_error"
        return code, desc[:200]
    return "unknown_error", text[:200]


def diagnose(status: int, code: str, grant_type: str, attempts: list) -> str:
    gt = grant_type or "?"
    tried = ", ".join("{0}:HTTP {1}/{2}".format(*a) for a in attempts) if attempts else "-"
    if code == "invalid_request":
        return (
            "Oura вернула 400 invalid_request. Два возможных источника: (1) malformed-"
            "запрос - лишний или продублированный параметр, PKCE code_verifier, тело не "
            "form-urlencoded, два механизма аутентификации сразу; (2) код, который Oura "
            "не может принять - истёк, уже использован или неизвестен. Проверено живьём "
            "11.09: Oura отвечает invalid_request и на нерабочий код тоже, поэтому одного "
            "этого кода ошибки недостаточно для вывода о форме запроса. Если в теле ровно "
            "grant_type/code/client_id/client_secret/redirect_uri, а код свежий - получи "
            "новый код через --authorize-url."
        )
    if code == "invalid_client":
        return (
            "Oura не приняла клиента (" + str(status) + " invalid_client). Проверь "
            "client_id/client_secret и способ аутентификации: ровно один - либо "
            "body, либо HTTP Basic. Попытки: " + tried + "."
        )
    if code == "invalid_grant":
        if gt == "authorization_code":
            return (
                "authorization code недействителен: уже использован (код одноразовый), "
                "истёк, redirect_uri не совпал символ-в-символ, или код выдан другому "
                "client_id. Получи НОВЫЙ код через authorization URL."
            )
        return (
            "refresh_token недействителен: уже использован (одноразовый) или отозван. "
            "Нужна повторная авторизация."
        )
    if code == "unsupported_grant_type":
        return "grant_type не поддерживается. Для кода: authorization_code; для обновления: refresh_token."
    if code == "malformed_request":
        return (
            "Oura не разобрала тело запроса (это не OAuth-ошибка, а отказ парсера). "
            "Проверь Content-Type: application/x-www-form-urlencoded и что тело URL-encoded."
        )
    if status == 403:
        return "403: нет прав / недостаточный scope. Проверь, какие scopes выданы приложению."
    if status == 429:
        return "429: rate limit Oura. Подожди и повтори."
    if status >= 500:
        return str(status) + ": ошибка на стороне Oura. Повтори позже."
    return "Неизвестный ответ Oura (HTTP " + str(status) + ", " + code + ")."


# --------------------------------------------------------------------------- #
# Token endpoint
# --------------------------------------------------------------------------- #

def _post_token(payload: dict, client_id: str, client_secret: str, use_basic: bool) -> requests.Response:
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/x-www-form-urlencoded",
    }
    body = dict(payload)
    auth = None
    if use_basic:
        auth = (client_id, client_secret)
    else:
        body["client_id"] = client_id
        body["client_secret"] = client_secret
    return requests.post(TOKEN_URL, data=body, headers=headers, auth=auth, timeout=HTTP_TIMEOUT)


def token_request(payload: dict, client_id: str, client_secret: str, grant_type: str) -> dict:
    """POST /oauth/token. Body credentials first; Basic as fallback ONLY.

    Never sends credentials twice, never adds parameters beyond the documented
    ones. Raises OuraOAuthError with an actionable diagnosis on failure.
    """
    attempts: list = []
    # Diagnostic: parameter NAMES only, never values. Proves the request shape.
    print("[oura] token request keys=" + ",".join(sorted(list(payload.keys()) + ["client_id", "client_secret"])) +
          " grant_type=" + str(payload.get("grant_type")), file=sys.stderr)
    resp = _post_token(payload, client_id, client_secret, use_basic=False)
    if resp.status_code < 400:
        return resp.json()
    code, desc = parse_error(resp.status_code, resp.text)
    attempts.append(("body", resp.status_code, code))

    if code == "invalid_client" and resp.status_code in (400, 401):
        resp2 = _post_token(payload, client_id, client_secret, use_basic=True)
        if resp2.status_code < 400:
            return resp2.json()
        code2, desc2 = parse_error(resp2.status_code, resp2.text)
        attempts.append(("basic", resp2.status_code, code2))
        raise OuraOAuthError(resp2.status_code, code2, desc2, diagnose(resp2.status_code, code2, grant_type, attempts))

    raise OuraOAuthError(resp.status_code, code, desc, diagnose(resp.status_code, code, grant_type, attempts))


def exchange_code(code: str, client_id: str, client_secret: str, redirect_uri: str) -> dict:
    """Exchange a fresh authorization code. The code is single-use."""
    payload = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": redirect_uri,
    }
    return token_request(payload, client_id, client_secret, "authorization_code")


def refresh_tokens(refresh_token: str, client_id: str, client_secret: str) -> dict:
    """Refresh the access token. Oura rotates refresh_token (single-use)."""
    payload = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
    }
    return token_request(payload, client_id, client_secret, "refresh_token")


# --------------------------------------------------------------------------- #
# state (CSRF) - generated before authorize, checked and burned on callback
# --------------------------------------------------------------------------- #

def new_state() -> str:
    return secrets.token_urlsafe(32)


def save_state(state: str, redirect_uri: str, scopes: list) -> None:
    data = {
        "state": state,
        "redirect_uri": redirect_uri,
        "scopes": list(scopes),
        "created_at": int(time.time()),
    }
    STATE_PATH.write_text(json.dumps(data), encoding="utf-8")
    os.chmod(STATE_PATH, 0o600)


def load_state() -> dict | None:
    if not STATE_PATH.exists():
        return None
    try:
        return json.loads(STATE_PATH.read_text(encoding="utf-8"))
    except Exception:
        return None


def consume_state(state: str) -> dict | None:
    """Validate the callback state and delete it (single use)."""
    data = load_state()
    if not data:
        return None
    # Validate FIRST, delete only when the state really is ours. Deleting before
    # validation would let any stray request burn a pending authorization.
    if not state or not secrets.compare_digest(str(data.get("state", "")), state):
        return None
    if int(time.time()) - int(data.get("created_at", 0)) > STATE_TTL_SECONDS:
        try:
            STATE_PATH.unlink()
        except OSError:
            pass
        return None
    try:
        STATE_PATH.unlink()
    except OSError:
        pass
    return data


def build_authorize_url(client_id: str, redirect_uri: str, scopes: list, state: str) -> str:
    params = {
        "response_type": "code",
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "state": state,
    }
    if scopes:
        params["scope"] = " ".join(scopes)
    # No scope parameter at all -> Oura requests every available scope.
    query = urllib.parse.urlencode(params, quote_via=urllib.parse.quote)
    return AUTHORIZE_URL + "?" + query


# --------------------------------------------------------------------------- #
# Token store + refresh-on-demand + API v2
# --------------------------------------------------------------------------- #

def save_tokens(env: dict, tokens: dict) -> dict:
    now = int(time.time())
    env["OURA_TOKEN_TYPE"] = str(tokens.get("token_type", "bearer"))
    env["OURA_ACCESS_TOKEN"] = str(tokens.get("access_token", ""))
    new_refresh = tokens.get("refresh_token")
    if new_refresh:
        env["OURA_REFRESH_TOKEN"] = str(new_refresh)
    env["OURA_TOKEN_EXPIRES_AT"] = str(now + int(tokens.get("expires_in", 86400)))
    env["OURA_TOKENS_OBTAINED_AT"] = str(now)
    if tokens.get("scope"):
        env["OURA_SCOPE"] = str(tokens["scope"])
    return env


def ensure_access_token(env: dict, force: bool = False) -> str:
    """Return a usable access token, refreshing (and persisting) when needed."""
    token = env.get("OURA_ACCESS_TOKEN", "")
    try:
        expires_at = int(env.get("OURA_TOKEN_EXPIRES_AT", "0") or 0)
    except ValueError:
        expires_at = 0
    if token and not force and time.time() < expires_at - REFRESH_SKEW_SECONDS:
        return token
    if not env.get("OURA_REFRESH_TOKEN"):
        raise OuraOAuthError(
            0, "no_refresh_token", "нет refresh_token",
            "Нужна повторная авторизация: получи новый code и обменяй его.",
        )
    tokens = refresh_tokens(env.get("OURA_REFRESH_TOKEN", ""), env.get("OURA_CLIENT_ID", ""), env.get("OURA_CLIENT_SECRET", ""))
    save_tokens(env, tokens)
    write_env(env)
    return env["OURA_ACCESS_TOKEN"]


def diagnose_api(status: int, url: str) -> str:
    """Actionable diagnosis for a v2 API error. Paths are case/underscore exact."""
    if status == 401:
        return ("401 даже после refresh: токен отозван или истёк. Нужна повторная "
                "авторизация (--authorize-url).")
    if status == 403:
        return ("403: этому приложению не выдан scope для эндпоинта. Проверь "
                "OURA_SCOPE и scopes, зарегистрированные для приложения.")
    if status == 404:
        return ("404: неверный путь эндпоинта. Oura различает регистр и подчёркивания: "
                "heartrate (без _), vO2_max (большая O). Проверь имя в " + url + ".")
    if status in (400, 422):
        return (str(status) + ": параметры запроса. Датовые эндпоинты ждут start_date/"
                "end_date, heartrate - start_datetime/end_datetime (ISO 8601).")
    if status == 429:
        return "429: rate limit Oura. Подожди и повтори."
    if status >= 500:
        return str(status) + ": ошибка на стороне Oura. Повтори позже."
    return "API v2 вернул HTTP " + str(status) + "."


def api_get(path: str, token: str, params: dict | None = None) -> requests.Response:
    url = path if path.startswith("http") else API_BASE + "/" + path.lstrip("/")
    return requests.get(
        url,
        headers={"Authorization": "Bearer " + token, "Accept": "application/json"},
        params=params or {},
        timeout=HTTP_TIMEOUT,
    )


def api_get_json(path: str, env: dict, params: dict | None = None) -> Any:
    """GET a v2 endpoint; on 401 refresh exactly once, then retry."""
    token = ensure_access_token(env)
    resp = api_get(path, token, params)
    if resp.status_code == 401:
        token = ensure_access_token(env, force=True)
        resp = api_get(path, token, params)
    if resp.status_code >= 400:
        raise OuraOAuthError(resp.status_code, "api_error", resp.text[:200],
                             diagnose_api(resp.status_code, url))
    return resp.json()
