#!/usr/bin/env python3
"""
Надёжный дайджест: собирает свежие посты Telegram-каналов и RSS,
формирует текст и отправляет владельцу через бота.

Использование:
  python3 digest.py            — собрать и отправить дайджест владельцу
  python3 digest.py --no-send  — только вывести текст (без отправки)
"""
from __future__ import annotations

import html
import json
import re
import sys
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Запуск из calendar/ не должен ломать импорт общего модуля workspace.
WORKSPACE_ROOT = Path(__file__).resolve().parents[1]
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

from services.digest.digest_utils import (  # noqa: E402
    WINDOW_HOURS,
    clip,
    extract_rss_titles,
    fetch_cached,
    summarize_source,
)

# SOCKS-прокси (Xray) не требуется: t.me/s отдаёт HTML напрямую.
SOCKS = None
CHANNELS = ["meduzalive", "istories_media", "thebell_io", "bazabazon"]
RSS_FEEDS = [
    ("РБК", "https://rssexport.rbc.ru/rbcnews/news/30/full.rss", 10),
    ("Коммерсантъ", "https://www.kommersant.ru/rss/news.xml", 10),
]
POSTS_PER_CHANNEL = 3
MAX_POST_LEN = 280

_CHANNEL_LABELS = {
    "meduzalive": "Медуза",
    "istories_media": "Важные истории",
    "thebell_io": "The Bell",
    "bazabazon": "BAZA",
}
_CHANNEL_EMOJI = {
    "meduzalive": "🟣",
    "istories_media": "🔵",
    "thebell_io": "🟠",
    "bazabazon": "⚫️",
}


def _clip(text: str, n: int = MAX_POST_LEN) -> str:
    """Compatibility wrapper for callers of the former helper."""
    return clip(text, n)


def _fetch_cached(url: str, curl_args: list[str], ttl: int = 900) -> str:
    """Compatibility wrapper using the shared bounded cache implementation."""
    return fetch_cached(url, curl_args, ttl)


def _rss(feed_url: str, limit: int | None = None, hours: int | None = None) -> list[tuple[str, datetime | None]]:
    """Return recent titles from an RSS feed, newest first."""
    effective_limit = RSS_FEEDS[0][2] if limit is None else limit
    effective_hours = WINDOW_HOURS if hours is None else hours
    try:
        data = fetch_cached(
            feed_url,
            ["curl", "-sL", "--max-time", "20", "-A", "Mozilla/5.0", feed_url],
        )
        return extract_rss_titles(data, hours=effective_hours, limit=effective_limit)
    except Exception as exc:
        print(f"RSS error {feed_url}: {exc}", file=sys.stderr)
        return []


def _curs() -> str:
    try:
        with urllib.request.urlopen(
            "https://www.cbr-xml-daily.ru/daily_json.js", timeout=15
        ) as response:
            values = json.load(response)["Valute"]
        return " · ".join(
            f"{code} {values[code]['Value']:.2f}" for code in ("USD", "EUR", "CNY")
        )
    except (OSError, KeyError, TypeError, ValueError):
        return "курс недоступен"


def _channel(
    channel: str,
    limit: int | None = None,
    hours: int | None = None,
) -> list[tuple[str, datetime | None]]:
    """Return distinct, recent Telegram channel posts ordered from newest to oldest."""
    effective_hours = WINDOW_HOURS if hours is None else hours
    effective_limit = POSTS_PER_CHANNEL if limit is None else limit
    cutoff = datetime.now(timezone.utc) - timedelta(hours=effective_hours)
    items: list[tuple[str, datetime | None]] = []
    seen: set[str] = set()
    try:
        url = f"https://t.me/s/{channel}"
        command = ["curl", "-s", "--max-time", "20", "-A", "Mozilla/5.0"]
        if SOCKS:
            command += ["--socks5-hostname", SOCKS]
        command.append(url)
        data = fetch_cached(url, command)
        for part in re.split(r'<div class="tgme_widget_message ', data)[1:]:
            date_match = re.search(r'datetime="([^"]+)"', part)
            text_match = re.search(
                r'tgme_widget_message_text[^>]*>(.*?)</div>', part, re.S
            )
            if not text_match:
                continue
            text = re.sub(r"<[^>]+>", " ", text_match.group(1))
            text = html.unescape(re.sub(r"\s+", " ", text)).strip()
            text = re.sub(
                r"НАСТОЯЩИЙ МАТЕРИАЛ.*?ИНОСТРАННОГО АГЕНТА[^.]*\.\s*", "", text
            )
            text = re.sub(r"18\+\s*", "", text).strip()
            if not text or text in seen or len(text) <= 25:
                continue
            published: datetime | None = None
            if date_match:
                try:
                    published = datetime.fromisoformat(
                        date_match.group(1).replace("Z", "+00:00")
                    )
                    if published.tzinfo is None:
                        published = published.replace(tzinfo=timezone.utc)
                    published = published.astimezone(timezone.utc)
                except ValueError:
                    pass
            if published and published < cutoff:
                continue
            seen.add(text)
            items.append((clip(text, MAX_POST_LEN), published))
    except Exception as exc:
        print(f"Channel error {channel}: {exc}", file=sys.stderr)

    items.sort(
        key=lambda pair: pair[1] or datetime.min.replace(tzinfo=timezone.utc),
        reverse=True,
    )
    return items[:effective_limit]


def _summarize_source(name: str, posts: list[tuple[str, datetime | None]]) -> str | None:
    """Compatibility wrapper for shared DeepSeek summary logic."""
    return summarize_source(name, [text for text, _ in posts])


def _collect_posts(hours: int) -> tuple[str, int]:
    """Collect raw posts in case a caller needs the pre-summary source text."""
    raw: list[str] = []
    for channel in CHANNELS:
        label = _CHANNEL_LABELS.get(channel, channel)
        posts = _channel(channel, hours=hours, limit=8)
        raw.extend(f"[{label}] {text}" for text, _ in posts)
    for name, url, limit in RSS_FEEDS:
        posts = _rss(url, limit=limit, hours=hours)
        raw.extend(f"[{name}] {text}" for text, _ in posts)
    return "\n".join(raw), len(raw)


def build(hours: int | None = None, use_ai: bool = True) -> str:
    """Build a digest grouped strictly by source."""
    effective_hours = WINDOW_HOURS if hours is None else hours
    if effective_hours <= 0:
        raise ValueError("hours должен быть положительным числом")

    lines = [f"<b>📰 Дайджест за последние {effective_hours} ч</b>", ""]
    sources: list[tuple[str, list[tuple[str, datetime | None]]]] = []
    for channel in CHANNELS:
        posts = _channel(channel, hours=effective_hours)
        if posts:
            title = f"{_CHANNEL_EMOJI.get(channel, '•')} {_CHANNEL_LABELS.get(channel, channel)}"
            sources.append((title, posts))
    for name, url, limit in RSS_FEEDS:
        posts = _rss(url, limit=limit, hours=effective_hours)
        if posts:
            sources.append((f"📡 {name}", posts))

    total = 0
    if not sources:
        lines.extend([f"За последние {effective_hours} ч свежих постов в каналах нет.", ""])
    else:
        for title, posts in sources:
            lines.append(title)
            summary = _summarize_source(title, posts) if use_ai else None
            if summary:
                lines.extend(line.strip() for line in summary.splitlines() if line.strip())
            else:
                lines.extend(f"   • {text}" for text, _ in posts)
            total += len(posts)
            lines.append("")

    lines.extend(
        [
            "━━━━━━━━━━━━━",
            "<b>💱 Курс (ЦБ):</b>",
            _curs(),
            f"⭐ Итого свежих постов: {total}",
        ]
    )
    return "\n".join(lines)


def send(text: str) -> str:
    calendar_dir = str(Path(__file__).resolve().parent)
    if calendar_dir not in sys.path:
        sys.path.insert(0, calendar_dir)
    import bot_sender

    return bot_sender.send_text_to_owner(text)


def main(argv: list[str] | None = None) -> int:
    arguments = list(sys.argv[1:] if argv is None else argv)
    hours = WINDOW_HOURS
    if "--hours" in arguments:
        try:
            position = arguments.index("--hours")
            hours = int(arguments[position + 1])
        except (IndexError, ValueError):
            print("Ошибка: --hours требует целое положительное значение", file=sys.stderr)
            return 2
    try:
        text = build(hours)
    except ValueError as exc:
        print(f"Ошибка: {exc}", file=sys.stderr)
        return 2
    print(text)
    if "--no-send" not in arguments:
        print("---")
        print(send(text))
    return 0


if __name__ == "__main__":
    sys.exit(main())
