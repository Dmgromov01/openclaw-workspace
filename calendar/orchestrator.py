#!/usr/bin/env python3
"""
Оркестратор: связывает парсер команд, календарь iCloud, .ics-генератор и отправку в Telegram.

Поток:
1. Парсит команду (встреча + ник + отправить мем/новости)
2. Добавляет событие в iCloud-календарь (Home)
3. Если указан ник участника:
   - генерирует .ics-файл приглашения
   - отправляет участнику уведомление о встрече + .ics через личный Telegram-аккаунт (Telethon)
4. Если команда "отправить мем": отправляет приложенный файл-мем участнику
5. Если команда "отправить новости": собирает новости из источника и отправляет

Использование:
  python3 orchestrator.py add "<текст команды>"
  python3 orchestrator.py check  — проверить авторизацию Telethon
"""

import sys
import os
import asyncio
import json
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from command_parser import parse_command
import icloud_calendar as cal
import ics_generator
import bot_sender  # схема: шлём приглашение владельцу через бота (для ручной пересылки)


def _load_attached_meme(text: str) -> str:
    """Возвращает путь к файлу-мему, если он указан (в реальном потоке файл приходит от пользователя).
    Заглушка: в CLI просто отмечаем, что мем будет приложен отдельно."""
    return None


async def process(text: str, meme_file: str = None) -> dict:
    """Главная функция обработки команды. Возвращает результат в виде dict."""
    res = parse_command(text)
    if not res["ok"]:
        return {"ok": False, "message": res["reason"] or "Не удалось разобрать команду"}

    summary = res["summary"]
    dt = res["dt"]
    username = res["username"]
    action = res["action"]
    action_arg = res["action_arg"]

    out = {
        "ok": True,
        "summary": summary,
        "dt": dt.strftime("%d.%m.%Y %H:%M"),
        "username": username,
        "action": action,
        "action_arg": action_arg,
        "messages": [],
    }

    # 1) Всегда добавляем событие в календарь
    ok_cal, msg_cal = cal.add_event(summary, dt)
    out["messages"].append(("calendar", f"📅 {msg_cal}" if ok_cal else f"❌ {msg_cal}"))
    if not ok_cal:
        # если в календарь не добавили, но есть адресат и команда — всё равно попробуем отправить
        pass

    # 2) Если есть адресат — шлём владельцу готовое приглашение (текст + .ics) для ручной пересылки
    if username:
        try:
            ics_path = ics_generator.save_ics(summary, dt, location=res.get("location") or "")
            note = (
                f"📅 Приглашение для @{username}\n"
                f"<b>{summary}</b>\n"
                f"🕐 {dt.strftime('%d.%m.%Y %H:%M')} MSK\n"
                f"Файл приглашения (.ics) — перешли, он добавит в свой календарь."
            )
            bot_sender.send_invite(username, note, ics_path)
            out["messages"].append(("tg_invite", f"✉️ Приглашение для @{username} отправлено тебе (текст + .ics)"))
        except Exception as e:
            out["messages"].append(("tg_error", f"⚠️ Ошибка формирования приглашения @{username}: {e}"))

    # 3) Команда "отправить мем"
    if action == "meme":
        if meme_file and os.path.exists(meme_file):
            if username:
                await tg_sender.send_file(username, meme_file, caption=action_arg or "Мем")
                out["messages"].append(("tg_meme", f"🖼 Мем отправлен @{username}"))
            else:
                out["messages"].append(("meme_warn", "⚠️ Указан мем, но нет адресата (@ник)"))
        else:
            out["messages"].append(("meme_warn", "⚠️ Мем указан, но файл не приложен. Приложи файл-мем."))

    # 4) Команда "отправить новости"
    if action == "news":
        src = action_arg or "сводка"
        if username:
            try:
                news = await _collect_news(src)
                await tg_sender.send_text(username, news)
                out["messages"].append(("tg_news", f"📰 Новости ({src}) отправлены @{username}"))
            except Exception as e:
                out["messages"].append(("tg_error", f"⚠️ Ошибка отправки новостей: {e}"))
        else:
            out["messages"].append(("news_warn", "⚠️ Новости указаны, но нет адресата (@ник)"))

    return out


async def _collect_news(source: str) -> str:
    """Собирает новости из источника. source: 'медуза', 'истории', 'the bell' и т.д.
    Пока заглушка: возвращает сводку из источников бота."""
    # TODO: реализовать реальный сбор новостей по источнику (Telethon подписки / web)
    return f"📰 Сводка новостей по источнику «{source}»: (сбор новостей будет реализован)"


async def check_auth() -> str:
    try:
        return await tg_sender.check_me()
    except Exception as e:
        return f"Ошибка авторизации Telethon: {e}"


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(2)
    cmd = sys.argv[1]
    if cmd == "check":
        print(asyncio.run(check_auth()))
    elif cmd == "add":
        text = " ".join(sys.argv[2:])
        res = asyncio.run(process(text))
        print(json.dumps(res, ensure_ascii=False, indent=2))
    else:
        print(__doc__)
        sys.exit(2)


if __name__ == "__main__":
    main()
