#!/usr/bin/env python3
"""Read and create Google Calendar events in Europe/Moscow."""
import argparse
import json
import os
import sys
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

CLIENT = "/root/.openclaw/credentials/gcal/oauth-client.json"
TOKENS = "/root/.openclaw/credentials/gcal/tokens.json"
CAL = "dmgromov03@gmail.com"
TZ = ZoneInfo("Europe/Moscow")
WEEKDAYS = ["пн", "вт", "ср", "чт", "пт", "сб", "вс"]
MONTHS = ["янв", "фев", "мар", "апр", "май", "июн", "июл", "авг", "сен", "окт", "ноя", "дек"]


def as_local(value: str) -> datetime:
    """Parse an API timestamp and normalize it to the configured display zone."""
    dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=TZ)
    return dt.astimezone(TZ)


def fmt_dow(value):
    return WEEKDAYS[value.weekday()]


def duration_min(event):
    try:
        start, end = event["start"].get("dateTime"), event["end"].get("dateTime")
        if not start or not end:
            return None
        return int((as_local(end) - as_local(start)).total_seconds() // 60)
    except (KeyError, TypeError, ValueError):
        return None


def line(event):
    start = event["start"].get("dateTime")
    if not start:
        return f"  • 🌐 {event.get('summary', '(без названия)')}"
    local = as_local(start)
    duration = duration_min(event)
    suffix = ""
    if duration and duration % 30 == 0 and duration <= 240:
        suffix = f" ({duration // 60}ч" + (f"{duration % 60}" if duration % 60 else "") + ")"
    location = f" — {event['location']}" if event.get("location") else ""
    return f"  • {local:%H:%M} {event.get('summary', '(без названия)')}{location}{suffix}"


def fetch(start, end, service):
    return service.events().list(calendarId=CAL, timeMin=start.isoformat(), timeMax=end.isoformat(), singleEvents=True, orderBy="startTime", maxResults=100).execute().get("items", [])


def cmd_today(service, now):
    start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    events = fetch(start, start + timedelta(days=1), service)
    if not events:
        return "📅 Сегодня событий нет."
    out = [f"📅 Сегодня, {fmt_dow(now)} {now.day} {MONTHS[now.month - 1]}:"]
    out.extend(line(event) for event in events)
    return "\n".join(out)


def cmd_week(service, now):
    start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    events = fetch(start, start + timedelta(days=7), service)
    byday = {}
    for event in events:
        event_start = event["start"].get("dateTime")
        if event_start:
            local_date = as_local(event_start).date()
            byday.setdefault(local_date, []).append(event)
    if not byday:
        return "📅 На ближайшие 7 дней событий нет."
    out = ["📅 Ближайшие 7 дней:"]
    for offset in range(7):
        date = start.date() + timedelta(days=offset)
        if date in byday:
            label = f"{fmt_dow(date)} {date.day} {MONTHS[date.month - 1]}"
            out.append(f"▸ {label}{' (сегодня)' if offset == 0 else ''}:")
            out.extend(line(event) for event in sorted(byday[date], key=lambda e: e["start"].get("dateTime", "")))
    return "\n".join(out)


def cmd_add(service, summary, start, end, location, description):
    body = {"summary": summary, "start": {"dateTime": start.isoformat(), "timeZone": "Europe/Moscow"}, "end": {"dateTime": end.isoformat(), "timeZone": "Europe/Moscow"}}
    if location:
        body["location"] = location
    if description:
        body["description"] = description
    event = service.events().insert(calendarId=CAL, body=body).execute()
    return f"✅ Событие создано: {event.get('summary')} — {as_local(event['start']['dateTime']):%H:%M}–{as_local(event['end']['dateTime']):%H:%M} (id: {event['id'][:8]})"


def load_service():
    if not (os.path.exists(TOKENS) and os.path.exists(CLIENT)):
        raise RuntimeError(f"нет OAuth-токенов ({TOKENS})")
    with open(TOKENS, encoding="utf-8") as handle:
        token_info = json.load(handle)
    with open(CLIENT, encoding="utf-8") as handle:
        client_info = json.load(handle).get("web", {})
    credentials = Credentials(token=token_info.get("access_token"), refresh_token=token_info.get("refresh_token"), token_uri=client_info.get("token_uri") or "https://oauth2.googleapis.com/token", client_id=client_info.get("client_id"), client_secret=client_info.get("client_secret"), scopes=["https://www.googleapis.com/auth/calendar"])
    if credentials.expired and credentials.refresh_token:
        credentials.refresh(Request())
        token_info["access_token"] = credentials.token
        with open(TOKENS, "w", encoding="utf-8") as handle:
            json.dump(token_info, handle)
    if not credentials.valid:
        raise RuntimeError(f"нет валидных OAuth-токенов ({TOKENS})")
    return build("calendar", "v3", credentials=credentials)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("cmd", choices=["today", "week", "list", "add"])
    parser.add_argument("args", nargs="*")
    parser.add_argument("--days", type=int, default=7)
    parser.add_argument("--location")
    parser.add_argument("--description")
    args = parser.parse_args()
    try:
        service = load_service()
    except (OSError, ValueError, RuntimeError) as exc:
        print(f"Ошибка: {exc}")
        return 2
    now = datetime.now(TZ)
    if args.cmd == "today":
        print(cmd_today(service, now))
    elif args.cmd == "week":
        print(cmd_week(service, now))
    elif args.cmd == "list":
        print(cmd_today(service, now) if args.days == 1 else cmd_week(service, now) if args.days == 7 else "\n".join(line(event) for event in fetch(now.replace(hour=0, minute=0, second=0, microsecond=0), now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=args.days), service)))
    else:
        if len(args.args) < 2:
            print('Использование: add "<summary>" "<YYYY-MM-DDTHH:MM>" ["<end>"]')
            return 2
        try:
            start = datetime.fromisoformat(args.args[1]).replace(tzinfo=TZ)
            end = datetime.fromisoformat(args.args[2]).replace(tzinfo=TZ) if len(args.args) >= 3 else start + timedelta(hours=1)
        except ValueError:
            print("Ошибка: дата должна быть в формате YYYY-MM-DDTHH:MM")
            return 2
        if end <= start:
            print("Ошибка: end должен быть позже start")
            return 2
        print(cmd_add(service, args.args[0], start, end, args.location, args.description))
    return 0


if __name__ == "__main__":
    sys.exit(main())
