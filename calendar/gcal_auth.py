#!/usr/bin/env python3
"""Перевыпуск OAuth-токена Google Calendar (console-flow, без браузера на хосте).

Запуск: python3 /root/openclaw/calendar/gcal_auth.py

1) скрипт напечатает ссылку — открой её в своём браузере и разреши доступ;
2) браузер уйдёт на http://localhost:47923/?code=... (страница не откроется — так и надо);
3) скопируй адрес из строки браузера целиком и вставь сюда;
4) скрипт обменяет код на токен и запишет tokens.json.

Важно: в Google Cloud → OAuth consent screen приложение должно быть в Production,
иначе refresh-токен снова умрёт через ~7 дней. Redirect URI
http://localhost:47923/ должен быть в списке Authorized redirect URIs клиента.
Зависимостей нет — только стандартная библиотека.
"""
from __future__ import annotations

import json
import os
import sys
import urllib.parse
import urllib.request

CLIENT = "/root/.openclaw/credentials/gcal/oauth-client.json"
TOKENS = "/root/.openclaw/credentials/gcal/tokens.json"
SCOPE = "https://www.googleapis.com/auth/calendar"
REDIRECT = "http://localhost:47923/"
TOKEN_URI = "https://oauth2.googleapis.com/token"


def main() -> int:
    if not os.path.exists(CLIENT):
        print(f"нет файла клиента: {CLIENT}", file=sys.stderr)
        return 2
    with open(CLIENT, encoding="utf-8") as fh:
        raw = json.load(fh)
    cfg = raw.get("installed") or raw.get("web") or raw
    client_id = cfg.get("client_id")
    client_secret = cfg.get("client_secret")
    if not client_id or not client_secret:
        print("в oauth-client.json нет client_id/client_secret", file=sys.stderr)
        return 2

    auth_url = "https://accounts.google.com/o/oauth2/v2/auth?" + urllib.parse.urlencode(
        {
            "client_id": client_id,
            "redirect_uri": REDIRECT,
            "response_type": "code",
            "scope": SCOPE,
            "access_type": "offline",
            "prompt": "consent",
        }
    )
    print("\n1) Открой ссылку в браузере и разреши доступ:\n")
    print(auth_url)
    print("\n2) После согласия браузер уйдёт на " + REDIRECT + "?code=... (страница не откроется — это нормально).")
    answer = input("3) Вставь сюда адрес из строки браузера (или сам код): ").strip()
    if not answer:
        print("пусто", file=sys.stderr)
        return 2

    code = answer
    if "code=" in answer:
        query = urllib.parse.urlparse(answer).query or answer.split("?", 1)[-1]
        code = (urllib.parse.parse_qs(query).get("code") or [""])[0]
    if not code:
        print("не нашёл code в строке", file=sys.stderr)
        return 2

    body = urllib.parse.urlencode(
        {
            "client_id": client_id,
            "client_secret": client_secret,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": REDIRECT,
        }
    ).encode()
    req = urllib.request.Request(TOKEN_URI, data=body, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            payload = json.load(resp)
    except Exception as exc:  # noqa: BLE001
        print(f"обмен кода не удался: {exc}", file=sys.stderr)
        return 3
    if not payload.get("refresh_token"):
        print("Google не вернул refresh_token — повтори (нужен prompt=consent)", file=sys.stderr)
        return 3

    out = {
        "access_token": payload.get("access_token"),
        "refresh_token": payload["refresh_token"],
        "scopes": [SCOPE],
        "token_uri": TOKEN_URI,
    }
    tmp = TOKENS + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=2)
    os.chmod(tmp, 0o600)
    os.replace(tmp, TOKENS)
    print(f"\nOK: новый токен записан в {TOKENS}")
    print("Проверка: python3 /root/openclaw/calendar/gcal_reader.py week")
    return 0


if __name__ == "__main__":
    sys.exit(main())
