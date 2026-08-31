#!/usr/bin/env python3
"""
Отправка приглашений через бота @Dmbotmy_bot (Bot API) — схема "дублирование владельцу".

Логика: когда пользователь создаёт встречу с @ником, бот шлёт ГОТОВОЕ приглашение
(текст + .ics-файл) на chat_id владельца. Владелец сам пересылает его контакту —
это обходит ограничение Telegram "бот не может писать первым".

Использование:
  python3 bot_sender.py send <username> "<текст>" <файл.ics>
  python3 bot_sender.py test   — проверить токен/доставку
"""

import json
import os
import sys
from pathlib import Path

# Запуск из calendar/ не должен ломать импорт общего модуля workspace.
WORKSPACE_ROOT = Path(__file__).resolve().parents[1]
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

from services.digest.secrets import read_secret_ref  # noqa: E402

OWNER_CHAT_ID = os.getenv("TG_OWNER_CHAT_ID", "1916536646")  # @Dm_GRM


def _get_token() -> str:
    cfg_path = WORKSPACE_ROOT.parent / ".openclaw" / "openclaw.json"
    with open(cfg_path) as f:
        cfg = json.load(f)
    tg = cfg.get("channels", {}).get("telegram", {})
    # новый формат: accounts.default.botToken
    tok = (tg.get("accounts", {}).get("default", {}) or {}).get("botToken", "")
    if not tok:
        tok = tg.get("botToken", "")
    # Единый резолвер секретов: строка или file-ссылка {source, id}.
    resolved = read_secret_ref(tok)
    if not resolved or resolved == "__OPENCLAW_REDACTED__":
        raise RuntimeError("botToken не найден в конфиге OpenClaw")
    return resolved


def _api(method: str, **params) -> dict:
    import urllib.error
    import urllib.parse
    import urllib.request

    tok = _get_token()
    url = f"https://api.telegram.org/bot{tok}/{method}"
    data = urllib.parse.urlencode(params).encode()
    req = urllib.request.Request(url, data=data)
    try:
        with urllib.request.urlopen(req, timeout=25) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as exc:
        body = exc.read().decode(errors="replace")
        raise RuntimeError(f"Telegram API {exc.code}: {body[:300]}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Telegram API недоступен: {exc.reason}") from exc


def send_text_to_owner(text: str) -> str:
    # Сначала пробуем с HTML; при 400 (битый HTML в контенте) — повторяем без parse_mode
    try:
        r = _api("sendMessage", chat_id=OWNER_CHAT_ID, text=text, parse_mode="HTML")
    except RuntimeError as exc:
        if "Telegram API 400" not in str(exc):
            raise
        r = _api("sendMessage", chat_id=OWNER_CHAT_ID, text=text)
    if not r.get("ok"):
        raise RuntimeError(f"sendMessage: {r.get('description')}")
    return f"OK message_id={r['result']['message_id']}"


def send_document_to_owner(path: str, caption: str = "") -> str:
    """Отправка файла .ics владельцу (multipart). Возвращает строку результата."""
    import requests

    tok = _get_token()
    url = f"https://api.telegram.org/bot{tok}/sendDocument"
    with open(path, "rb") as f:
        files = {"document": (os.path.basename(path), f, "text/calendar")}
        data = {"chat_id": OWNER_CHAT_ID}
        if caption:
            data["caption"] = caption
        resp = requests.post(url, files=files, data=data, timeout=30)
    r = resp.json()
    if not r.get("ok"):
        raise RuntimeError(f"sendDocument: {r.get('description')}")
    return f"OK message_id={r['result']['message_id']}"


def send_invite(username: str, text: str, ics_path: str) -> str:
    """Шлёт владельцу: сначала текст приглашения (с @ником), затем .ics-файл."""
    r1 = send_text_to_owner(text)
    r2 = send_document_to_owner(ics_path, caption=f"📎 {username} — приглашение в календарь")
    return f"{r1} | {r2}"


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(2)
    cmd = sys.argv[1]
    try:
        if cmd == "test":
            print("Токен OK, шлю тест-текст владельцу...")
            print(send_text_to_owner("🤖 Тест: отправка приглашений владельцу работает."))
        elif cmd == "send":
            username = sys.argv[2]
            text = sys.argv[3]
            ics = sys.argv[4] if len(sys.argv) > 4 else None
            if ics:
                print(send_invite(username, text, ics))
            else:
                print(send_text_to_owner(text))
        else:
            print(__doc__)
            sys.exit(2)
    except Exception as e:
        print(f"Ошибка: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
