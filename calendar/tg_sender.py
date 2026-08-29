#!/usr/bin/env python3
"""
Отправка сообщений через ЛИЧНЫЙ Telegram-аккаунт (Telethon) — для доставки
новым участникам, которые не знают бота.

Требует TG_API_ID / TG_API_HASH в /root/tg_bot/.env + рабочую сессию anon_session.session.
Перед отправкой получатель должен быть явно внесён в TG_ALLOWED_RECIPIENTS
(список username или numeric ID через запятую) в том же .env.

Использование:
  python3 tg_sender.py send <username> "<текст>"
  python3 tg_sender.py send_file <username> <путь_к_файлу> ["<подпись>"]
  python3 tg_sender.py send_photo <username> <путь_к_картинке> ["<подпись>"]
  python3 tg_sender.py me    — проверить авторизацию
"""

import asyncio
import os
import sys

from dotenv import load_dotenv

load_dotenv("/root/tg_bot/.env")

TG_API_ID = os.getenv("TG_API_ID", "").strip()
TG_API_HASH = os.getenv("TG_API_HASH", "").strip()
TG_ALLOWED_RECIPIENTS = frozenset(
    item.strip().lstrip("@").lower()
    for item in os.getenv("TG_ALLOWED_RECIPIENTS", "").split(",")
    if item.strip()
)


def _recipient_key(value: str) -> str:
    return str(value).strip().lstrip("@").lower()


def _ensure_allowed(recipient: str) -> None:
    """Fail closed unless the recipient is explicitly configured as trusted."""
    key = _recipient_key(recipient)
    if not TG_ALLOWED_RECIPIENTS:
        raise RuntimeError(
            "TG_ALLOWED_RECIPIENTS не задан: сначала явно настрой список разрешённых получателей."
        )
    if key not in TG_ALLOWED_RECIPIENTS:
        raise RuntimeError(f"Получатель не входит в TG_ALLOWED_RECIPIENTS: {recipient}")


def _make_client():
    import python_socks
    from telethon import TelegramClient

    if not TG_API_ID or not TG_API_HASH:
        raise RuntimeError(
            "TG_API_ID / TG_API_HASH не заданы в /root/tg_bot/.env. "
            "Получи их на https://my.telegram.org (API development tools)."
        )
    proxy = {
        "proxy_type": python_socks.ProxyType.SOCKS5,
        "addr": "127.0.0.1",
        "port": 4001,
        "rdns": True,
    }
    return TelegramClient(
        "/root/tg_bot/anon_session",
        int(TG_API_ID),
        TG_API_HASH,
        proxy=proxy,
    )


async def _resolve_entity(client, username: str):
    """Разрешает username в entity. Поддерживает @nick и число (id)."""
    u = username.strip()
    if u.startswith("@"):
        u = u[1:]
    try:
        return await client.get_entity(u)
    except Exception as exc:
        raise RuntimeError(f"Не удалось найти пользователя @{u}: {exc}") from exc


async def _send_text(client, entity, text: str):
    await client.send_message(entity, text)


async def _send_file(client, entity, path: str, caption: str = ""):
    if not os.path.exists(path):
        raise RuntimeError(f"Файл не найден: {path}")
    await client.send_file(entity, path, caption=caption or None)


async def send_text(username: str, text: str) -> str:
    _ensure_allowed(username)
    client = _make_client()
    await client.connect()
    try:
        entity = await _resolve_entity(client, username)
        await _send_text(client, entity, text)
        uname = getattr(entity, "username", None) or str(username)
        return f"Сообщение отправлено @{uname}"
    finally:
        await client.disconnect()


async def send_file(username: str, path: str, caption: str = "") -> str:
    _ensure_allowed(username)
    client = _make_client()
    await client.connect()
    try:
        entity = await _resolve_entity(client, username)
        await _send_file(client, entity, path, caption)
        uname = getattr(entity, "username", None) or str(username)
        return f"Файл отправлен @{uname}"
    finally:
        await client.disconnect()


async def check_me() -> str:
    client = _make_client()
    await client.connect()
    try:
        me = await client.get_me()
        return f"Авторизован: {me.first_name} @{me.username}"
    finally:
        await client.disconnect()


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    cmd = sys.argv[1]

    try:
        if cmd == "me":
            print(asyncio.run(check_me()))
        elif cmd == "send" and len(sys.argv) >= 4:
            print(asyncio.run(send_text(sys.argv[2], sys.argv[3])))
        elif cmd == "send_file" and len(sys.argv) >= 4:
            caption = sys.argv[4] if len(sys.argv) > 4 else ""
            print(asyncio.run(send_file(sys.argv[2], sys.argv[3], caption)))
        elif cmd == "send_photo" and len(sys.argv) >= 4:
            caption = sys.argv[4] if len(sys.argv) > 4 else ""
            print(asyncio.run(send_file(sys.argv[2], sys.argv[3], caption)))
        else:
            print(__doc__)
            return 2
    except Exception as exc:
        print(f"Ошибка: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
