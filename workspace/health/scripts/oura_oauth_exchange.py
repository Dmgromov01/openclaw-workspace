#!/usr/bin/env python3
"""Oura OAuth2 helper --- authorize URL, code exchange, credentials, diagnostics.

Runs on the Gateway host. Never prints secrets. Modes:

    --authorize-url      print a fresh authorization URL (saves CSRF state)
    --code CODE          exchange an authorization code for tokens (code is single-use)
    --set-credentials    prompt (hidden) for client_id/client_secret, store 0600
    --oauth-check        verify the whole configuration, print JSON, no secrets
    --api-check          with stored tokens: hit API v2 personal_info + daily_readiness
"""
from __future__ import annotations

import argparse
import getpass
import json
import sys
import time

import oura_auth as oa


def out(obj: dict) -> None:
    print(json.dumps(obj, ensure_ascii=False, indent=2))


def resolve_client_id(args) -> str:
    if args.client_id:
        return args.client_id
    env = oa.read_env()
    return env.get("OURA_CLIENT_ID", "")


def cmd_set_credentials(args) -> int:
    env = oa.read_env()
    client_id = args.client_id or input("Oura client_id: ").strip()
    secret = getpass.getpass("Oura client_secret (hidden, not echoed): ").strip()
    if not client_id or not secret:
        print("client_id и client_secret обязательны", file=sys.stderr)
        return 2
    env["OURA_CLIENT_ID"] = client_id
    env["OURA_CLIENT_SECRET"] = secret
    oa.write_env(env)
    out({"ok": True, "stored": str(oa.ENV_PATH), "chmod": "600",
         "client_id_length": len(client_id), "client_secret_length": len(secret)})
    return 0


def cmd_authorize_url(args) -> int:
    client_id = resolve_client_id(args)
    if not client_id:
        print("нет client_id: передай --client-id или сначала --set-credentials", file=sys.stderr)
        return 2
    redirect_uri = args.redirect_uri or oa.DEFAULT_REDIRECT_URI
    if args.scopes and args.scopes.strip().lower() == "all":
        scopes = []   # omit scope -> Oura grants every available scope
    elif args.scopes and args.scopes.strip():
        scopes = args.scopes.split(",")
    else:
        scopes = list(oa.DEFAULT_SCOPES)
    state = oa.new_state()
    oa.save_state(state, redirect_uri, scopes)
    url = oa.build_authorize_url(client_id, redirect_uri, scopes, state)
    out({"authorize_url": url, "redirect_uri": redirect_uri, "scopes": scopes,
         "state_saved": True, "state_ttl_seconds": oa.STATE_TTL_SECONDS})
    return 0


def cmd_exchange(args) -> int:
    env = oa.read_env()
    client_id = resolve_client_id(args) or env.get("OURA_CLIENT_ID", "")
    redirect_uri = args.redirect_uri or env.get("OURA_REDIRECT_URI") or oa.DEFAULT_REDIRECT_URI
    if not client_id:
        print("нет client_id", file=sys.stderr)
        return 2
    secret = env.get("OURA_CLIENT_SECRET") or getpass.getpass("Oura client_secret (hidden): ").strip()
    if not secret:
        print("нет client_secret", file=sys.stderr)
        return 2

    # Diagnostic header: never log the code or the secret itself.
    print("[oauth] POST " + oa.TOKEN_URL, file=sys.stderr)
    print("[oauth] Content-Type: application/x-www-form-urlencoded", file=sys.stderr)
    print("[oauth] grant_type: authorization_code", file=sys.stderr)
    print("[oauth] code_present: " + str(bool(args.code)), file=sys.stderr)
    print("[oauth] code_length: " + str(len(args.code or "")), file=sys.stderr)
    print("[oauth] client_id_present: True", file=sys.stderr)
    print("[oauth] client_secret_present: True", file=sys.stderr)
    print("[oauth] redirect_uri: " + redirect_uri, file=sys.stderr)

    try:
        tokens = oa.exchange_code(args.code, client_id, secret, redirect_uri)
    except oa.OuraOAuthError as exc:
        out({"ok": False, "status": exc.status, "error": exc.code,
             "error_description": exc.description, "diagnosis": exc.diagnosis})
        return 1

    env["OURA_CLIENT_ID"] = client_id
    env["OURA_CLIENT_SECRET"] = secret
    env["OURA_REDIRECT_URI"] = redirect_uri
    oa.save_tokens(env, tokens)
    oa.write_env(env)
    # A code that worked is now burned: drop any pending state.
    try:
        oa.STATE_PATH.unlink()
    except OSError:
        pass
    out({"ok": True, "has_refresh_token": bool(env.get("OURA_REFRESH_TOKEN")),
         "expires_at": env.get("OURA_TOKEN_EXPIRES_AT"),
         "token_type": env.get("OURA_TOKEN_TYPE"), "scope": env.get("OURA_SCOPE", ""),
         "stored": str(oa.ENV_PATH)})
    return 0


def cmd_oauth_check(args) -> int:
    env = oa.read_env()
    checks = []
    env_exists = oa.ENV_PATH.exists()

    def add(name, ok, detail):
        checks.append({"check": name, "ok": bool(ok), "detail": detail})

    add("env_file", env_exists, str(oa.ENV_PATH) + (" (нет --- нужен --set-credentials)" if not env_exists else ""))
    add("client_id", bool(env.get("OURA_CLIENT_ID")), "OURA_CLIENT_ID: " + ("есть" if env.get("OURA_CLIENT_ID") else "нет"))
    add("client_secret", bool(env.get("OURA_CLIENT_SECRET")), "OURA_CLIENT_SECRET: " + ("есть" if env.get("OURA_CLIENT_SECRET") else "нет"))
    redirect_uri = env.get("OURA_REDIRECT_URI") or oa.DEFAULT_REDIRECT_URI
    add("redirect_uri", redirect_uri.endswith("/"), redirect_uri + " (должен совпадать с Oura символ-в-символ)")
    add("authorize_url", True, oa.AUTHORIZE_URL)
    add("token_url", True, oa.TOKEN_URL)
    add("api_base", True, oa.API_BASE)
    add("token_body_format", True, "application/x-www-form-urlencoded, параметры только из доков")
    add("pkce_disabled", not oa.STATE_PATH.name.startswith(".pkce"), "PKCE не используется (Oura его не поддерживает)")
    add("token_storage", env_exists, str(oa.ENV_PATH) + " (chmod 600), ключи OURA_*")
    add("access_token", bool(env.get("OURA_ACCESS_TOKEN")), "наличие access_token")
    add("refresh_token", bool(env.get("OURA_REFRESH_TOKEN")), "наличие refresh_token (single-use)")
    expires_at = env.get("OURA_TOKEN_EXPIRES_AT", "")
    add("expires_at", bool(expires_at), expires_at or "нет")
    pending = oa.load_state()
    add("pending_state", bool(pending), ("ожидает callback, создан " + str(pending.get("created_at")) if pending else "нет ожидающего state"))

    # Live connectivity to the Oura API (no credentials needed for the 401 probe).
    import requests
    try:
        resp = requests.get(oa.API_BASE + "/personal_info", headers={"Accept": "application/json"}, timeout=15)
        add("api_reachable", resp.status_code in (200, 401), "HTTP " + str(resp.status_code) + " (401 = достижимо, токен не отправлялся)")
    except Exception as exc:
        add("api_reachable", False, "нет связи: " + str(exc)[:120])

    ok = all(c["ok"] for c in checks if c["check"] not in ("access_token", "refresh_token"))
    out({"ok": ok, "checks": checks})
    return 0 if ok else 1


def cmd_api_check(args) -> int:
    env = oa.read_env()
    results = []
    for name, path, params in (
        ("personal_info", "personal_info", None),
        ("daily_sleep", "daily_sleep", {"start_date": time.strftime("%Y-%m-%d", time.gmtime(time.time() - 7 * 86400)),
                                        "end_date": time.strftime("%Y-%m-%d", time.gmtime())}),
        ("daily_readiness", "daily_readiness", None),
    ):
        try:
            data = oa.api_get_json(path, env, params)
            n = len(data.get("data", [])) if isinstance(data, dict) else 0
            results.append({"endpoint": name, "ok": True, "items": n})
        except oa.OuraOAuthError as exc:
            results.append({"endpoint": name, "ok": False, "status": exc.status, "diagnosis": exc.diagnosis})
    out({"ok": all(r["ok"] for r in results), "results": results})
    return 0 if all(r["ok"] for r in results) else 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Oura OAuth2 helper")
    parser.add_argument("--code", help="authorization code from the redirect URL")
    parser.add_argument("--client-id", help="Oura OAuth client_id (not secret)")
    parser.add_argument("--redirect-uri", help="must match the registered URI exactly")
    parser.add_argument("--scopes", help="comma-separated scopes")
    parser.add_argument("--authorize-url", action="store_true", help="print a new authorization URL")
    parser.add_argument("--set-credentials", action="store_true", help="prompt for and store client credentials")
    parser.add_argument("--oauth-check", action="store_true", help="configuration self-check (no secrets)")
    parser.add_argument("--api-check", action="store_true", help="live API v2 check with stored tokens")
    args = parser.parse_args()

    if args.set_credentials:
        return cmd_set_credentials(args)
    if args.oauth_check:
        return cmd_oauth_check(args)
    if args.api_check:
        return cmd_api_check(args)
    if args.authorize_url:
        return cmd_authorize_url(args)
    if args.code:
        return cmd_exchange(args)
    parser.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
