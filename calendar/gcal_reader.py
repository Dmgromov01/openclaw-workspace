#!/usr/bin/env python3
"""
Чтение и создание событий Google Calendar dmgromov03@gmail.com.
Команды:
  today  — события на сегодня
  week   — события на ближайшие 7 дней
  list --days N — события на N дней
  add "<summary>" "<start>" ["<end>"] [--location "..."] [--description "..."]
      — Создать событие. start/end — в формате YYYY-MM-DDTHH:MM (Europe/Moscow).
        end по умолчанию = start + 1 час.
Вывод в человекочитаемом виде.
"""
import argparse
import sys
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

# pip install google-api-python-client google-auth

from google.oauth2 import service_account
from googleapiclient.discovery import build

KEY = "/root/.openclaw/credentials/gcal/service-account.json"
CAL = "dmgromov03@gmail.com"
TZ = ZoneInfo("Europe/Moscow")

WEEKDAYS = ["пн", "вт", "ср", "чт", "пт", "сб", "вс"]
MONTHS = ["янв", "фев", "мар", "апр", "май", "июн",
          "июл", "авг", "сен", "окт", "ноя", "дек"]


def fmt_date(d):
    return f"{d.day} {MONTHS[d.month - 1]}"


def fmt_dow(d):
    return WEEKDAYS[d.weekday()]


def duration_min(ev):
    try:
        s = ev["start"].get("dateTime")
        e = ev["end"].get("dateTime")
        if not s or not e:
            return None
        sd = datetime.fromisoformat(s)
        ed = datetime.fromisoformat(e)
        return int((ed - sd).total_seconds() // 60)
    except Exception:
        return None


def line(ev):
    s = ev["start"].get("dateTime")
    if not s:
        return f"  • 🌐 {ev.get('summary','(без названия)')}"
    dt = datetime.fromisoformat(s)
    hm = dt.strftime("%H:%M")
    dur = duration_min(ev)
    parts = []
    if dur and dur % 30 == 0 and dur <= 240:
        parts.append(f"{dur // 60}ч" if dur % 60 == 0 else f"{dur // 60}ч{dur % 60}")
    suffix = f" ({', '.join(parts)})" if parts else ""
    loc = f" — {ev.get('location')}" if ev.get("location") else ""
    return f"  • {hm} {ev.get('summary','(без названия)')}{loc}{suffix}"


def _build(creds):
    return build("calendar", "v3", credentials=creds)


def fetch(start, end, svc):
    r = svc.events().list(
        calendarId=CAL,
        timeMin=start.isoformat(),
        timeMax=end.isoformat(),
        singleEvents=True,
        orderBy="startTime",
        maxResults=100,
    ).execute()
    return r.get("items", [])


def cmd_today(svc, now):
    start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end = start + timedelta(days=1)
    evs = fetch(start, end, svc)
    if not evs:
        return "📅 Сегодня событий нет."
    out = [f"📅 Сегодня, {fmt_dow(now)} {now.day} {MONTHS[now.month - 1]}:"]
    for e in evs:
        out.append(line(e))
    return "\n".join(out)


def cmd_week(svc, now):
    # группируем по дням
    start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end = start + timedelta(days=7)
    evs = fetch(start, end, svc)
    if not evs:
        return "📅 На ближайшие 7 дней событий нет."
    # группировка
    byday = {}
    for e in evs:
        s = e["start"].get("dateTime")
        if not s:
            continue
        d = datetime.fromisoformat(s).date()
        byday.setdefault(d, []).append(e)
    out = ["📅 Ближайшие 7 дней:"]
    cur = start.date()
    for i in range(7):
        d = cur + timedelta(days=i)
        if d in byday:
            label = f"{fmt_dow(d)} {d.day} {MONTHS[d.month - 1]}"
            if i == 0:
                label += " (сегодня)"
            out.append(f"▸ {label}:")
            for e in sorted(byday[d], key=lambda x: x["start"].get("dateTime", "")):
                out.append(line(e))
    return "\n".join(out)


def cmd_add(svc, summary, start, end, location, description):
    body = {
        "summary": summary,
        "start": {"dateTime": start.strftime("%Y-%m-%dT%H:%M:%S"), "timeZone": "Europe/Moscow"},
        "end": {"dateTime": end.strftime("%Y-%m-%dT%H:%M:%S"), "timeZone": "Europe/Moscow"},
    }
    if location:
        body["location"] = location
    if description:
        body["description"] = description
    ev = svc.events().insert(calendarId=CAL, body=body).execute()
    s = datetime.fromisoformat(ev["start"]["dateTime"]).strftime("%H:%M")
    e = datetime.fromisoformat(ev["end"]["dateTime"]).strftime("%H:%M")
    return f"✅ Событие создано: {ev.get('summary')} — {s}–{e} (id: {ev['id'][:8]})"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["today", "week", "list", "add"])
    ap.add_argument("args", nargs="*", help="для add: summary start [end]")
    ap.add_argument("--days", type=int, default=7)
    ap.add_argument("--location")
    ap.add_argument("--description")
    a = ap.parse_args()

    creds = service_account.Credentials.from_service_account_file(
        KEY, scopes=["https://www.googleapis.com/auth/calendar"]
    )
    svc = _build(creds)
    now = datetime.now(TZ)

    if a.cmd == "today":
        print(cmd_today(svc, now))
    elif a.cmd == "week":
        print(cmd_week(svc, now))
    elif a.cmd == "add":
        if len(a.args) < 2:
            print("Использование: add \"<summary>\" \"<YYYY-MM-DDTHH:MM>\" [\"<end>\"] --location ... --description ...")
            sys.exit(2)
        summary = a.args[0]
        try:
            start = datetime.fromisoformat(a.args[1]).replace(tzinfo=TZ)
        except ValueError:
            print("Ошибка: start должен быть в формате YYYY-MM-DDTHH:MM")
            sys.exit(2)
        if len(a.args) >= 3:
            try:
                end = datetime.fromisoformat(a.args[2]).replace(tzinfo=TZ)
            except ValueError:
                print("Ошибка: end должен быть в формате YYYY-MM-DDTHH:MM")
                sys.exit(2)
        else:
            end = start + timedelta(hours=1)
        if end <= start:
            print("Ошибка: end должен быть позже start")
            sys.exit(2)
        print(cmd_add(svc, summary, start, end, a.location, a.description))
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end = start + timedelta(days=a.days)
        evs = fetch(start, end, svc)
        if not evs:
            print(f"📅 На {a.days} дней событий нет.")
        else:
            for e in evs:
                print(line(e))


if __name__ == "__main__":
    main()
