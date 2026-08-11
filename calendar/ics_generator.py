#!/usr/bin/env python3
"""
Генератор .ics-приглашения для событий календаря.
Создаёт валидный iCalendar-файл (RFC 5545), который можно открыть на iPhone
и добавить в календарь.
"""

import sys
import uuid
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from pathlib import Path

MOSCOW_TZ = ZoneInfo("Europe/Moscow")
OUT_DIR = Path("/root/.openclaw/workspace/calendar/ics")


def _format_dt_utc(dt: datetime) -> str:
    """Формат UTC для iCalendar: YYYYMMDDTHHMMSSZ"""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=MOSCOW_TZ)
    dt_utc = dt.astimezone(ZoneInfo("UTC"))
    return dt_utc.strftime("%Y%m%dT%H%M%SZ")


def generate_ics(summary: str, start_dt: datetime, duration_minutes: int = 60,
                 description: str = "", location: str = "") -> str:
    """
    Генерирует содержимое .ics-файла. Возвращает строку.
    """
    end_dt = start_dt + timedelta(minutes=duration_minutes)
    uid = str(uuid.uuid4()) + "@openclaw-calendar"
    now = datetime.now(MOSCOW_TZ)

    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//OpenClaw//iCloud Calendar//RU",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        "BEGIN:VEVENT",
        f"UID:{uid}",
        f"DTSTAMP:{_format_dt_utc(now)}",
        f"DTSTART:{_format_dt_utc(start_dt)}",
        f"DTEND:{_format_dt_utc(end_dt)}",
        f"SUMMARY:{summary}",
    ]
    if location:
        lines.append(f"LOCATION:{location}")
    if description:
        # экранируем и убираем переносы
        desc = description.replace("\n", "\\n").replace(",", "\\,").replace(";", "\\;")
        lines.append(f"DESCRIPTION:{desc}")
    lines.append("END:VEVENT")
    lines.append("END:VCALENDAR")

    return "\r\n".join(lines) + "\r\n"


def _safe_filename(text: str) -> str:
    """Транслитерирует и делает безопасное имя файла (латиница, без пробелов)."""
    translit = {
        'а':'a','б':'b','в':'v','г':'g','д':'d','е':'e','ё':'e','ж':'zh','з':'z',
        'и':'i','й':'y','к':'k','л':'l','м':'m','н':'n','о':'o','п':'p','р':'r',
        'с':'s','т':'t','у':'u','ф':'f','х':'h','ц':'ts','ч':'ch','ш':'sh','щ':'sch',
        'ъ':'','ы':'y','ь':'','э':'e','ю':'yu','я':'ya',' ':'_','\t':'_',
    }
    out = []
    for ch in text.lower():
        if ch.isalnum():
            out.append(ch)
        elif ch in translit:
            out.append(translit[ch])
        else:
            out.append('_')
    return ''.join(out)[:40].strip('_')


def save_ics(summary: str, start_dt: datetime, duration_minutes: int = 60,
             description: str = "", location: str = "") -> str:
    """Сохраняет .ics в файл и возвращает путь."""
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    content = generate_ics(summary, start_dt, duration_minutes, description, location)
    safe = _safe_filename(summary) or "event"
    fname = f"{start_dt.strftime('%Y%m%d_%H%M')}_{safe}.ics"
    path = OUT_DIR / fname
    path.write_text(content, encoding="utf-8")
    return str(path)


if __name__ == "__main__":
    # CLI: summary "DD.MM.YYYY HH:MM" [minutes]
    if len(sys.argv) < 3:
        print("Использование: python3 ics_generator.py \"<summary>\" \"<DD.MM.YYYY HH:MM>\" [minutes] [location]", file=sys.stderr)
        sys.exit(2)
    summary = sys.argv[1]
    when = sys.argv[2]
    minutes = int(sys.argv[3]) if len(sys.argv) > 3 else 60
    location = sys.argv[4] if len(sys.argv) > 4 else ""
    try:
        dt = datetime.strptime(when, "%d.%m.%Y %H:%M").replace(tzinfo=MOSCOW_TZ)
    except ValueError:
        print("Формат даты: DD.MM.YYYY HH:MM", file=sys.stderr)
        sys.exit(2)
    path = save_ics(summary, dt, minutes, location=location)
    print(path)
