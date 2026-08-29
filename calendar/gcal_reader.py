#!/usr/bin/env python3
"""Read and create Google Calendar events in Europe/Moscow."""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

CLIENT = "/root/.openclaw/credentials/gcal/oauth-client.json"
TOKENS = "/root/.openclaw/credentials/gcal/tokens.json"
CAL = "dmgromov03@gmail.com"
TZ = ZoneInfo("Europe/Moscow")
WEEKDAYS = ["пн", "вт", "ср", "чт", "пт", "сб", "вс"]
MONTHS = ["янв", "фев", "мар", "апр", "май", "июн", "июл", "авг", "сен", "окт", "ноя", "дек"]
MAX_LIST_DAYS = 90


def as_local(value: str) -> datetime:
    """Parse an API timestamp and normalize it to the configured display zone."""
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=TZ)
    return parsed.astimezone(TZ)


def parse_event_datetime(value: str) -> datetime:
    """Parse CLI input, preserving an explicit UTC offset if one was supplied."""
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=TZ)
    return parsed.astimezone(TZ)


def fmt_dow(value: date | datetime) -> str:
    return WEEKDAYS[value.weekday()]


def event_date(event: dict) -> date | None:
    """Return the local calendar date for timed and all-day Google events."""
    start = event.get("start", {})
    if start.get("dateTime"):
        return as_local(start["dateTime"]).date()
    if start.get("date"):
        try:
            return date.fromisoformat(start["date"])
        except ValueError:
            return None
    return None


def duration_min(event: dict) -> int | None:
    try:
        start = event["start"].get("dateTime")
        end = event["end"].get("dateTime")
        if not start or not end:
            return None
        return int((as_local(end) - as_local(start)).total_seconds() // 60)
    except (KeyError, TypeError, ValueError):
        return None


def line(event: dict) -> str:
    start = event.get("start", {}).get("dateTime")
    title = event.get("summary", "(без названия)")
    if not start:
        return f"  • 🌐 {title}"
    local = as_local(start)
    duration = duration_min(event)
    suffix = ""
    if duration and duration % 30 == 0 and duration <= 240:
        suffix = f" ({duration // 60}ч" + (f"{duration % 60}" if duration % 60 else "") + ")"
    location = f" — {event['location']}" if event.get("location") else ""
    return f"  • {local:%H:%M} {title}{location}{suffix}"


def fetch(start: datetime, end: datetime, service) -> list[dict]:
    return service.events().list(
        calendarId=CAL,
        timeMin=start.isoformat(),
        timeMax=end.isoformat(),
        singleEvents=True,
        orderBy="startTime",
        maxResults=100,
    ).execute().get("items", [])


def _events_by_day(events: list[dict]) -> dict[date, list[dict]]:
    grouped: dict[date, list[dict]] = {}
    for event in events:
        local_date = event_date(event)
        if local_date is not None:
            grouped.setdefault(local_date, []).append(event)
    return grouped


def _format_days(events: list[dict], start: datetime, days: int, heading: str) -> str:
    grouped = _events_by_day(events)
    if not grouped:
        return f"📅 {heading}: событий нет."
    output = [f"📅 {heading}:"]
    for offset in range(days):
        current = start.date() + timedelta(days=offset)
        if current not in grouped:
            continue
        label = f"{fmt_dow(current)} {current.day} {MONTHS[current.month - 1]}"
        output.append(f"▸ {label}{' (сегодня)' if offset == 0 else ''}:")
        output.extend(
            line(event)
            for event in sorted(
                grouped[current], key=lambda item: item.get("start", {}).get("dateTime", "")
            )
        )
    return "\n".join(output)


def cmd_today(service, now: datetime) -> str:
    start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    events = fetch(start, start + timedelta(days=1), service)
    if not events:
        return "📅 Сегодня событий нет."
    output = [f"📅 Сегодня, {fmt_dow(now)} {now.day} {MONTHS[now.month - 1]}:"]
    output.extend(line(event) for event in events)
    return "\n".join(output)


def cmd_week(service, now: datetime) -> str:
    start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    return _format_days(fetch(start, start + timedelta(days=7), service), start, 7, "Ближайшие 7 дней")


def cmd_list(service, now: datetime, days: int) -> str:
    start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    if days == 1:
        return cmd_today(service, now)
    if days == 7:
        return cmd_week(service, now)
    return _format_days(
        fetch(start, start + timedelta(days=days), service),
        start,
        days,
        f"Ближайшие {days} дней",
    )


def cmd_add(
    service,
    summary: str,
    start: datetime,
    end: datetime,
    location: str | None,
    description: str | None,
) -> str:
    body = {
        "summary": summary,
        "start": {"dateTime": start.isoformat(), "timeZone": "Europe/Moscow"},
        "end": {"dateTime": end.isoformat(), "timeZone": "Europe/Moscow"},
    }
    if location:
        body["location"] = location
    if description:
        body["description"] = description
    event = service.events().insert(calendarId=CAL, body=body).execute()
    return (
        f"✅ Событие создано: {event.get('summary')} — "
        f"{as_local(event['start']['dateTime']):%H:%M}–"
        f"{as_local(event['end']['dateTime']):%H:%M} (id: {event['id'][:8]})"
    )


def load_service():
    """Load and refresh the OAuth credential only when a Google call is requested."""
    if not (os.path.exists(TOKENS) and os.path.exists(CLIENT)):
        raise RuntimeError(f"нет OAuth-токенов ({TOKENS})")
    try:
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build
    except ImportError as exc:
        raise RuntimeError("не установлены зависимости Google Calendar API") from exc

    with open(TOKENS, encoding="utf-8") as handle:
        token_info = json.load(handle)
    with open(CLIENT, encoding="utf-8") as handle:
        client_info = json.load(handle).get("web", {})
    credentials = Credentials(
        token=token_info.get("access_token"),
        refresh_token=token_info.get("refresh_token"),
        token_uri=client_info.get("token_uri") or "https://oauth2.googleapis.com/token",
        client_id=client_info.get("client_id"),
        client_secret=client_info.get("client_secret"),
        scopes=["https://www.googleapis.com/auth/calendar"],
    )
    if credentials.expired and credentials.refresh_token:
        credentials.refresh(Request())
        token_info["access_token"] = credentials.token
        with open(TOKENS, "w", encoding="utf-8") as handle:
            json.dump(token_info, handle)
    if not credentials.valid:
        raise RuntimeError(f"нет валидных OAuth-токенов ({TOKENS})")
    return build("calendar", "v3", credentials=credentials)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("cmd", choices=["today", "week", "list", "add"])
    parser.add_argument("args", nargs="*")
    parser.add_argument("--days", type=int, default=7)
    parser.add_argument("--location")
    parser.add_argument("--description")
    args = parser.parse_args(argv)
    if not 1 <= args.days <= MAX_LIST_DAYS:
        parser.error(f"--days должен быть от 1 до {MAX_LIST_DAYS}")
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
        print(cmd_list(service, now, args.days))
    else:
        if len(args.args) < 2:
            print('Использование: add "<summary>" "<YYYY-MM-DDTHH:MM>" ["<end>"]')
            return 2
        try:
            start = parse_event_datetime(args.args[1])
            end = parse_event_datetime(args.args[2]) if len(args.args) >= 3 else start + timedelta(hours=1)
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
