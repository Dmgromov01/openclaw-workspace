"""News-digest retrieval, parsing, and summarization helpers."""
from __future__ import annotations

import hashlib
import html
import json
import logging
import os
import re
import subprocess
import urllib.request
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from typing import Sequence

from services.digest.secrets import deepseek_config

logger = logging.getLogger("digest")
WINDOW_HOURS = 2
CACHE_DIR = "/root/.openclaw/cache"
CACHE_TTL = 900


def clip(text: str, max_len: int = 400) -> str:
    """Trim text at a word boundary without returning an overlong result."""
    text = (text or "").strip()
    if len(text) <= max_len:
        return text
    truncated = text[: max(1, max_len - 1)]
    return (truncated.rsplit(" ", 1)[0] or truncated).rstrip() + "…"


def fetch_cached(url: str, command: Sequence[str], ttl: int = CACHE_TTL) -> str:
    """Run a bounded fetch command and cache non-trivial responses briefly."""
    cache_file = os.path.join(
        CACHE_DIR, f"digest_{hashlib.sha256(url.encode('utf-8')).hexdigest()}.cache"
    )
    try:
        os.makedirs(CACHE_DIR, exist_ok=True)
        if (
            os.path.exists(cache_file)
            and datetime.now().timestamp() - os.path.getmtime(cache_file) < ttl
        ):
            with open(cache_file, encoding="utf-8") as handle:
                return handle.read()
    except OSError:
        # The digest remains useful even if the optional cache is unavailable.
        pass

    try:
        result = subprocess.run(
            list(command),
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        logger.warning("Fetch failed for %s: %s", url, exc)
        return ""

    data = result.stdout
    if data and len(data) > 100:
        try:
            with open(cache_file, "w", encoding="utf-8") as handle:
                handle.write(data)
        except OSError:
            pass
    return data


def extract_rss_titles(
    data: str,
    hours: int = WINDOW_HOURS,
    limit: int = 10,
) -> list[tuple[str, datetime | None]]:
    """Return recent RSS item titles ordered from newest to oldest."""
    import xml.etree.ElementTree as ET

    root = ET.fromstring(data)
    now = datetime.now(timezone.utc)
    items: list[tuple[str, datetime | None]] = []
    for item in (node for node in root.iter() if node.tag.split("}")[-1] == "item"):
        fields = {
            child.tag.split("}")[-1]: child.text or ""
            for child in item
        }
        title = re.sub(r"\s+", " ", html.unescape(fields.get("title", ""))).strip()
        if not title or len(title) <= 15 or title == "Коммерсантъ. Лента новостей":
            continue

        published: datetime | None = None
        value = fields.get("pubDate")
        if value:
            try:
                published = parsedate_to_datetime(value)
                if published.tzinfo is None:
                    published = published.replace(tzinfo=timezone.utc)
                published = published.astimezone(timezone.utc)
            except (TypeError, ValueError, IndexError):
                logger.debug("Could not parse RSS date %r", value)
        if published and published < now - timedelta(hours=hours):
            continue
        items.append((clip(title, 280), published))

    items.sort(
        key=lambda pair: pair[1] or datetime.min.replace(tzinfo=timezone.utc),
        reverse=True,
    )
    return items[:limit]


def summarize_source(source: str, texts: list[str]) -> str | None:
    """Create a concise factual Russian-language summary for one source."""
    content = "\n".join(text for text in texts if text).strip()
    if not content:
        return None

    api_key, base_url = deepseek_config()
    if not api_key:
        logger.warning("DeepSeek credentials are unavailable; skipping AI summary")
        return None

    payload = json.dumps(
        {
            "model": "deepseek-chat",
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "Ты — редактор дайджеста. Перед тобой посты одного источника. "
                        "Составь краткое саммари на русском: максимум 3–4 предложения, "
                        "только суть. Сохрани ключевые факты и цифры; не искажай смысл "
                        "и ничего не выдумывай. Не перечисляй посты списком."
                    ),
                },
                {"role": "user", "content": f"Источник: {source}\n{content}"},
            ],
            "temperature": 0.3,
            "max_tokens": 300,
        }
    ).encode("utf-8")
    request = urllib.request.Request(
        f"{base_url.rstrip('/')}/chat/completions",
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            decoded = json.loads(response.read().decode("utf-8"))
        return decoded["choices"][0]["message"]["content"].strip() or None
    except (OSError, ValueError, KeyError, IndexError, TypeError) as exc:
        logger.warning("Digest summarization failed for %s: %s", source, exc)
        return None
