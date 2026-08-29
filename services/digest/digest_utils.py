"""News digest pipeline utilities."""
from __future__ import annotations

import html
import json
import logging
import os
import re
import subprocess
import urllib.request
from email.utils import parsedate_to_datetime
from datetime import datetime, timedelta, timezone

from services.digest.secrets import deepseek_config

logger = logging.getLogger("digest")
WINDOW_HOURS = 2
CACHE_DIR = "/root/.openclaw/cache"
CACHE_TTL = 900


def clip(text: str, max_len: int = 400) -> str:
    text = text or ""
    if len(text) <= max_len:
        return text
    return text[:max_len].rsplit(" ", 1)[0].rstrip() + "…"


def fetch_cached(url: str, command: list[str], ttl: int = CACHE_TTL) -> str:
    os.makedirs(CACHE_DIR, exist_ok=True)
    import hashlib
    cache_file = os.path.join(CACHE_DIR, f"digest_{hashlib.sha256(url.encode()).hexdigest()}.cache")
    try:
        if os.path.exists(cache_file) and datetime.now().timestamp() - os.path.getmtime(cache_file) < ttl:
            with open(cache_file, encoding="utf-8") as handle:
                return handle.read()
    except OSError:
        pass

    result = subprocess.run(command, capture_output=True, text=True, timeout=30, check=False)
    data = result.stdout
    if data and len(data) > 100:
        try:
            with open(cache_file, "w", encoding="utf-8") as handle:
                handle.write(data)
        except OSError:
            pass
    return data


def extract_rss_titles(data: str, hours: int = WINDOW_HOURS, limit: int = 10) -> list[tuple[str, datetime | None]]:
    import xml.etree.ElementTree as ET
    root = ET.fromstring(data)
    now = datetime.now(timezone.utc)
    items: list[tuple[str, datetime | None]] = []
    for item in root.iter("item"):
        title = next((child.text or "" for child in item if child.tag.split("}")[-1] == "title"), "")
        title = re.sub(r"\s+", " ", html.unescape(title)).strip()
        if not title or len(title) <= 15 or title == "Коммерсантъ. Лента новостей":
            continue
        published = None
        for child in item:
            if child.tag.split("}")[-1] == "pubDate" and child.text:
                try:
                    published = parsedate_to_datetime(child.text)
                    if published.tzinfo is None:
                        published = published.replace(tzinfo=timezone.utc)
                    published = published.astimezone(timezone.utc)
                except (TypeError, ValueError, IndexError):
                    pass
        if published and published < now - timedelta(hours=hours):
            continue
        items.append((clip(title, 280), published))
    items.sort(key=lambda pair: pair[1] or datetime.min.replace(tzinfo=timezone.utc), reverse=True)
    return items[:limit]


def summarize_source(source: str, texts: list[str]) -> str | None:
    content = "\n".join(texts).strip()
    if not content:
        return None
    key, base_url = deepseek_config()
    if not key:
        return None
    payload = json.dumps({
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": "Сожми новости одного источника на русском в 3–4 предложения. Сохрани ключевые факты и цифры, ничего не выдумывай."},
            {"role": "user", "content": f"Источник: {source}\n{content}"},
        ],
        "temperature": 0.3,
        "max_tokens": 300,
    }).encode()
    request = urllib.request.Request(
        f"{base_url}/chat/completions",
        data=payload,
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {key}"},
    )
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            return json.loads(response.read().decode())["choices"][0]["message"]["content"].strip()
    except Exception as exc:
        logger.warning("Digest summarization failed for %s: %s", source, exc)
        return None
