#!/usr/bin/env python3
"""
Надёжный доступ к календарю iCloud (CalDAV) для OpenClaw.

Вариант А: вся логика календаря работает здесь, bot.py остановлен.
Использует календарь "Home" из .env бота (ICLOUD_CALENDAR_URL), не полагаясь
на ошибочный выбор calendars[0] из старого bot.py.

Команды (CLI):
  list            — показать события на сегодня
  list --days N   — показать события на N дней (--days 7 = неделя)
  add "<summary>" "<DD.MM.YYYY HH:MM>" [minutes]
  delete "<search>"  — удалить события, где SUMMARY/дата содержит search
  delete --date "<DD.MM.YYYY>"  — удалить все события за дату
  today | week | month  — сокращения
"""

import os
import sys
import re
import argparse
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import caldav
from dotenv import load_dotenv

# Секреты читаем из .env старого бота (не дублируем, не логируем)
ENV_PATH = "/root/tg_bot/.env"
load_dotenv(ENV_PATH)

ICLOUD_USERNAME = os.getenv("ICLOUD_USERNAME", "").strip()
ICLOUD_PASSWORD = os.getenv("ICLOUD_PASSWORD", "").strip()
ICLOUD_CALENDAR_URL = os.getenv("ICLOUD_CALENDAR_URL", "").strip()

MOSCOW_TZ = ZoneInfo("Europe/Moscow")

# Календарь по умолчанию: берём из ICLOUD_CALENDAR_URL, иначе первый writable "Home"
DEFAULT_CAL_PATH = ICLOUD_CALENDAR_URL if ICLOUD_CALENDAR_URL else "/calendars/home/"


def _client():
    if not ICLOUD_USERNAME or not ICLOUD_PASSWORD:
        raise RuntimeError("ICLOUD_USERNAME/ICLOUD_PASSWORD не заданы в .env")
    return caldav.DAVClient(
        url="https://caldav.icloud.com",
        username=ICLOUD_USERNAME,
        password=ICLOUD_PASSWORD,
    )


def _calendar(client):
    """Возвращает целевой календарь (Home)."""
    # Берём конкретный календарь по пути, если он задан
    if ICLOUD_CALENDAR_URL:
        path = ICLOUD_CALENDAR_URL
        # нормализуем: убираем ведущий '/', добавляем к базовому URL
        base = "https://caldav.icloud.com"
        cal_url = path if path.startswith("http") else base + (path if path.startswith("/") else "/" + path)
        try:
            return caldav.Calendar(client=client, url=cal_url)
        except Exception as e:
            raise RuntimeError(f"Не удалось открыть календарь {cal_url}: {e}")

    # Фолбэк: ищем календарь по названию, содержащему "home"/"календарь", иначе первый
    principal = client.principal()
    cals = principal.calendars()
    for c in cals:
        name = ""
        try:
            name = c.get_display_name() or ""
        except Exception:
            name = ""
        if "home" in name.lower() or "основн" in name.lower():
            return c
    if cals:
        return cals[0]
    raise RuntimeError("Не найдено ни одного календаря")


def _parse_event_dt(event):
    """Достаёт DTSTART и SUMMARY из сырого VEVENT. Возвращает (dt, summary) или None."""
    try:
        raw = str(event.data)
    except Exception:
        return None

    # SUMMARY
    m = re.search(r"SUMMARY(?:;[^:]*)?:(.*?)(?:\r?\n|$)", raw)
    summary = None
    if m:
        summary = m.group(1).strip().replace("\\,", ",").replace("\\;", ";")
        # убираем возможный хвост следующего поля (если SUMMARY не на отдельной строке)
        summary = re.split(r"\r?\n[A-Z]", summary)[0].strip()

    # DTSTART: поддержка YYYYMMDD и YYYYMMDDTHHMMSS, а также TZID/смещений
    m = re.search(r"DTSTART(?:;[^:]*)?:?(\d{8})(?:T(\d{6}))?", raw)
    if not m:
        return None
    date_part = m.group(1)
    time_part = m.group(2)
    try:
        y, mo, d = int(date_part[:4]), int(date_part[4:6]), int(date_part[6:8])
        if time_part:
            hh, mm = int(time_part[:2]), int(time_part[2:4])
            dt = datetime(y, mo, d, hh, mm, tzinfo=MOSCOW_TZ)
        else:
            dt = datetime(y, mo, d, tzinfo=MOSCOW_TZ)  # весь день
    except ValueError:
        return None
    return dt, summary


def fetch_events(days: int = 1):
    """Возвращает список (dt, summary) за ближайшие `days` дней (включая сегодня).
    Использует cal.events() + локальную фильтрацию — устойчиво к 412 и пустым календарям."""
    client = _client()
    cal = _calendar(client)
    now = datetime.now(MOSCOW_TZ)
    start = now.date()
    end = now.date() + timedelta(days=days)

    events = []
    try:
        results = cal.events()
    except Exception as e:
        raise RuntimeError(f"Ошибка получения событий: {e}")

    for ev in results:
        parsed = _parse_event_dt(ev)
        if parsed and parsed[0] is not None:
            dt = parsed[0]
            # отсекаем явный мусор (даты вне разумного диапазона, напр. 1880)
            if dt.year < 1990 or dt.year > 2100:
                continue
            if start <= dt.date() <= end:
                events.append(parsed)
    events.sort(key=lambda x: (x[0].date(), x[0].time() if x[0].time() else datetime.min.time()))
    return events


def add_event(summary: str, start_dt: datetime, duration_minutes: int = 60):
    """Добавляет событие. Возвращает (ok, message)."""
    try:
        client = _client()
        cal = _calendar(client)
        if start_dt.tzinfo is None:
            start_dt = start_dt.replace(tzinfo=MOSCOW_TZ)
        end_dt = start_dt + timedelta(minutes=duration_minutes)
        cal.save_event(dtstart=start_dt, dtend=end_dt, summary=summary)
        return True, f"Событие «{summary}» добавлено на {start_dt.strftime('%d.%m.%Y %H:%M')}"
    except Exception as e:
        return False, str(e)


def delete_events(search: str = None, on_date=None):
    """Удаляет события. search — по SUMMARY, on_date — по дате (date). Возвращает (ok, count).
    Использует cal.events() + локальную фильтрацию (устойчиво к 412)."""
    client = _client()
    cal = _calendar(client)

    deleted = 0
    try:
        results = cal.events()
    except Exception as e:
        raise RuntimeError(f"Ошибка получения событий для удаления: {e}")

    for ev in results:
        parsed = _parse_event_dt(ev)
        if not parsed or parsed[0] is None:
            continue
        dt, summary = parsed
        if dt.year < 1990 or dt.year > 2100:
            continue
        summary_l = (summary or "").lower()
        match = False
        if search:
            match = search.lower() in summary_l
        elif on_date is not None:
            match = dt.date() == on_date
        if match:
            try:
                ev.delete()
                deleted += 1
            except Exception as e:
                print(f"  ! не удалось удалить «{summary}»: {e}", file=sys.stderr)
    return True, deleted


def format_schedule(events, title):
    if not events:
        return title + "\n\nНет встреч."
    lines = [title]
    for dt, summary in events:
        d = dt.date()
        if dt.time() == datetime.min.time():
            lines.append(f"• {d.strftime('%d.%m.%Y')} — {summary} [весь день]")
        else:
            lines.append(f"• {dt.strftime('%d.%m.%Y %H:%M')} — {summary}")
    return "\n".join(lines)


def parse_datetime(text: str):
    """Разбирает 'действие + дата + время'. Возвращает (summary, datetime) или (None, None)."""
    t = text.strip()
    if not t:
        return None, None

    # 1) DD.MM.YYYY (или DD.MM.YY) + время HH:MM — где угодно в строке
    # дата
    dm = re.search(r"(\d{1,2})\.(\d{1,2})\.(\d{2,4})", t)
    # время
    tm = re.search(r"(\d{1,2}):(\d{2})", t)
    if dm:
        day, mon, year = int(dm.group(1)), int(dm.group(2)), int(dm.group(3))
        if year < 100:
            year = 2000 + year
        hh, mm = 9, 0
        if tm:
            hh, mm = int(tm.group(1)), int(tm.group(2))
        try:
            dt = datetime(year, mon, day, hh, mm, tzinfo=MOSCOW_TZ)
            # summary = всё, кроме найденной даты и времени
            summary = re.sub(r"\s*(\d{1,2}\.\d{1,2}\.\d{2,4})\s*", " ", t)
            summary = re.sub(r"\s*(\d{1,2}:\d{2})\s*", " ", summary)
            summary = re.sub(r"\bв\b", "", summary, flags=re.IGNORECASE)
            summary = summary.strip().strip(".,").strip()
            if not summary:
                summary = "Новая встреча"
            return summary, dt
        except ValueError:
            return None, None

    # 2) относительные: сегодня/завтра/послезавтра + время
    low = t.lower()
    now = datetime.now(MOSCOW_TZ)
    target = None
    if "послезавтра" in low:
        target = now + timedelta(days=2)
    elif "завтра" in low:
        target = now + timedelta(days=1)
    elif "сегодня" in low or "сейчас" in low:
        target = now
    if target and tm:
        hh, mm = int(tm.group(1)), int(tm.group(2))
        dt = target.replace(hour=hh, minute=mm, second=0, microsecond=0)
        summary = re.sub(r"\s*(\d{1,2}:\d{2})\s*", " ", t)
        summary = re.sub(r"\b(сегодня|завтра|послезавтра|сейчас|в)\b", "", summary, flags=re.IGNORECASE)
        summary = summary.strip().strip(".,").strip()
        if not summary:
            summary = "Новая встреча"
        return summary, dt

    return None, None


def main():
    p = argparse.ArgumentParser(description="iCloud CalDAV для OpenClaw")
    sub = p.add_subparsers(dest="cmd")

    sub.add_parser("today", help="события на сегодня")
    sub.add_parser("week", help="события на неделю (7 дней)")
    sub.add_parser("month", help="события на месяц (30 дней)")

    pl = sub.add_parser("list", help="события на N дней")
    pl.add_argument("--days", type=int, default=1)

    pa = sub.add_parser("add", help="добавить событие")
    pa.add_argument("summary")
    pa.add_argument("when", help="DD.MM.YYYY HH:MM")
    pa.add_argument("minutes", nargs="?", type=int, default=60)

    pd = sub.add_parser("delete", help="удалить события")
    pd.add_argument("--search", help="подстрока в названии")
    pd.add_argument("--date", help="DD.MM.YYYY — удалить события за этот день")

    args = p.parse_args()

    try:
        if args.cmd in ("today", "list"):
            days = 1 if args.cmd == "today" else args.days
            events = fetch_events(days)
            print(format_schedule(events, ""))
        elif args.cmd == "week":
            events = fetch_events(7)
            print(format_schedule(events, ""))
        elif args.cmd == "month":
            events = fetch_events(30)
            print(format_schedule(events, "📅 Расписание на месяц:"))
        elif args.cmd == "add":
            summary, dt = parse_datetime(f"{args.summary} {args.when}")
            if not dt:
                # пробуем распарсить when напрямую
                ok, dt = False, None
                try:
                    dt = datetime.strptime(args.when, "%d.%m.%Y %H:%M").replace(tzinfo=MOSCOW_TZ)
                    ok = True
                except Exception:
                    ok = False
                if not ok:
                    print("Не удалось разобрать дату. Формат: DD.MM.YYYY HH:MM", file=sys.stderr)
                    sys.exit(2)
            ok, msg = add_event(summary, dt, args.minutes)
            print(msg)
            sys.exit(0 if ok else 1)
        elif args.cmd == "delete":
            if args.date:
                try:
                    dd = datetime.strptime(args.date, "%d.%m.%Y").date()
                except Exception:
                    print("Формат даты: DD.MM.YYYY", file=sys.stderr)
                    sys.exit(2)
                ok, n = delete_events(on_date=dd)
                print(f"Удалено событий за {args.date}: {n}")
            else:
                ok, n = delete_events(search=args.search)
                print(f"Удалено событий по запросу «{args.search}»: {n}")
            sys.exit(0 if ok else 1)
        else:
            p.print_help()
    except Exception as e:
        print(f"Ошибка: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
