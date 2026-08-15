#!/usr/bin/env python3
"""
Надёжный дайджест: парсит последние посты из TG-каналов (t.me/s через VPN SOCKS)
+ берёт курс валют ЦБ, формирует чистый текст и отправляет владельцу через бота.

Использование:
  python3 digest.py            — собрать и отправить дайджест владельцу
  python3 digest.py --no-send  — только вывести текст (без отправки)
"""
import sys
import re
import html
import json
import subprocess
import urllib.request

# SOCKS-прокси (Xray) НЕ требуется: t.me/s отдаёт HTML напрямую.
# На сервере Xray не запущен (порт 10808 закрыт) — запросы идут без прокси.
SOCKS = None
CHANNELS = ["meduzalive", "istories_media", "thebell_io", "bazabazon"]
# RSS-фиды: (название, url, лимит постов)
RSS_FEEDS = [
    ("РБК", "https://rssexport.rbc.ru/rbcnews/news/30/full.rss", 10),
    ("Коммерсантъ", "https://www.kommersant.ru/rss/news.xml", 10),
]
OWNER = "1916536646"

# Окно времени для "дайджеста за последние N часов" (по умолчанию 2)
WINDOW_HOURS = 2

# Постов на канал (увеличено: объём +50%, было по 2)
POSTS_PER_CHANNEL = 3
# Максимум символов на пост (обрезка) — увеличен для полноты текста
MAX_POST_LEN = 280


# ---------- RSS-фиды ----------
def _rss(feed_url: str, limit: int = None, hours: int = None) -> list:
    """Возвращает [(текст, время)] заголовков из RSS-фида."""
    import datetime as _dt
    hours = WINDOW_HOURS if hours is None else hours
    limit = RSS_FEEDS[0][2] if limit is None else limit
    cut = 30
    try:
        curl = ["curl", "-sL", "--max-time", "20", "-A", "Mozilla/5.0", feed_url]
        r = subprocess.run(curl, capture_output=True, text=True)
        data = r.stdout
        import xml.etree.ElementTree as ET
        root = ET.fromstring(data)
        items = []
        now = _dt.datetime.now(_dt.timezone.utc)
        for it in root.iter("item"):
            t = ""
            for child in it:
                tag = child.tag.split("}")[-1]
                if tag == "title":
                    t = (child.text or "").strip()
                elif tag == "pubDate" and not (child.text or "").startswith("20"):
                    pass
            if t == "Коммерсантъ. Лента новостей":
                continue
            t = re.sub(r"\s+", " ", html.unescape(t)).strip()
            if not t or len(t) <= 15:
                continue
            # дата — RFC822 пары (GMT); русские СМИ часто шлют без зоны
            post_dt = None
            for child in it:
                if child.tag.split("}")[-1] == "pubDate" and child.text:
                    try:
                        import email.utils as _eu
                        post_dt = _dt.datetime(*_eu.parsedate(child.text)[:6], tzinfo=_dt.timezone.utc)
                    except Exception:
                        post_dt = None
            if hours is not None and post_dt is not None and post_dt < now - _dt.timedelta(hours=hours):
                continue
            items.append((t[:MAX_POST_LEN], post_dt))
        items.sort(key=lambda x: (x[1] is None, -(x[1].timestamp() if x[1] else 0)))
        return items[:limit]
    except Exception as e:
        print(f"RSS error {feed_url}: {e}")
        return []


# ---------- Курс ЦБ ----------
def _curs() -> str:
    try:
        d = json.load(urllib.request.urlopen("https://www.cbr-xml-daily.ru/daily_json.js", timeout=15))
        v = d["Valute"]
        def fmt(k):
            return f"{v[k]['Value']:.2f}".replace(".", ".")
        return f"USD {v['USD']['Value']:.2f} · EUR {v['EUR']['Value']:.2f} · CNY {v['CNY']['Value']:.2f}"
    except Exception:
        return "курс недоступен"


# ---------- Парсинг канала -----
def _channel(ch: str, limit: int = None, hours: int = None) -> list:
    """Возвращает (текст, время) постов канала за последние `hours` часов,
    отсортированные по свежести (новые первыми).
    Если hours не задан (None) — берём просто последние посты."""
    import datetime as _dt
    hours = WINDOW_HOURS if hours is None else hours
    limit = POSTS_PER_CHANNEL if limit is None else limit
    cutoff = _dt.datetime.now(_dt.timezone.utc) - _dt.timedelta(hours=hours)
    items = []
    try:
        curl = ["curl", "-s", "--max-time", "20", "-A", "Mozilla/5.0"]
        if SOCKS:
            curl += ["--socks5-hostname", SOCKS]
        curl.append(f"https://t.me/s/{ch}")
        r = subprocess.run(curl, capture_output=True, text=True)
        data = r.stdout
        parts = re.split(r'<div class="tgme_widget_message ', data)
        seen = set()
        for p in parts[1:]:
            dts = re.search(r'datetime="([^"]+)"', p)
            mtxt = re.search(r'tgme_widget_message_text[^>]*>(.*?)</div>', p, re.S)
            if not mtxt:
                continue
            t = re.sub(r"<[^>]+>", " ", mtxt.group(1))
            t = html.unescape(re.sub(r"\s+", " ", t)).strip()
            t = re.sub(r"НАСТОЯЩИЙ МАТЕРИАЛ.*?ИНОСТРАННОГО АГЕНТА[^.]*\.\s*", "", t)
            t = re.sub(r"18\+\s*", "", t).strip()
            # отбрасываем слишком короткие/служебные
            if not t or t in seen or len(t) <= 25:
                continue
            # время поста
            post_dt = None
            if dts:
                try:
                    post_dt = _dt.datetime.fromisoformat(dts.group(1).replace("Z", "+00:00"))
                except Exception:
                    post_dt = None
            if hours is not None and post_dt is not None and post_dt < cutoff:
                continue
            seen.add(t)
            items.append((t, post_dt))
    except Exception:
        pass
    # сортировка по свежести (новые первыми); без даты — в конец
    items.sort(key=lambda x: (x[1] is None, -(x[1].timestamp() if x[1] else 0)))
    return [(t[:MAX_POST_LEN], d) for t, d in items[:limit]]


# ---------- ИИ-саммари (DeepSeek) ----------
def _ai_summarize(posts_text: str) -> str:
    """Прогоняет сырые посты через DeepSeek и возвращает краткое саммари."""
    try:
        cfg = json.load(open("/root/.openclaw/openclaw.json"))
        keys = cfg.get("models", {}).get("providers", {}).get("deepseek", {})
        api_key = keys.get("apiKey")
        # apiKey может быть объектом file-provider: {"source": "file", "id": "/deepseek_key"}
        if isinstance(api_key, dict):
            # ищем реальный ключ в secrets (все известные места)
            found = None
            import os
            for sp in ["/etc/openclaw/secrets.json", "/root/.openclaw/secrets/secrets.json", "/root/.openclaw/secrets.json"]:
                if os.path.exists(sp):
                    try:
                        sd = json.load(open(sp))
                        # ключ может лежать по id или по имени
                        if api_key.get("id"):
                            sid = api_key["id"].lstrip("/")
                            if sid in sd:
                                found = sd[sid]; break
                        # fallback: ищем любое значение, начинающееся на sk-
                        def find_sk(o):
                            if isinstance(o, str):
                                return o if o.startswith("sk-") else None
                            if isinstance(o, dict):
                                for v in o.values():
                                    r = find_sk(v)
                                    if r: return r
                            return None
                        if not found:
                            found = find_sk(sd)
                    except Exception:
                        continue
            api_key = found
        base_url = keys.get("baseUrl", "https://api.deepseek.com/").rstrip("/") + "/v1"
        if not api_key:
            return None
        payload = json.dumps({
            "model": "deepseek-chat",
            "messages": [
                {"role": "system", "content": (
                    "Ты — редактор новостного дайджеста. Из списка сырых постов составь подробное, "
                    "точное саммари на русском. СОХРАНЯЙ исходный контекст: не пересказывай своими словами "
                    "и не упрощай смысл — передавай факты так, как они изложены в оригинале (кто, что, где, "
                    "цифры, детали). ВКЛЮЧАЙ как можно больше значимой информации."
                    "ГРУППИРУЙ СТРОГО ПО ИСТОЧНИКАМ, НЕ ПО ТЕМАТИКЕ: каждый источник — отдельный блок "
                    "с заголовком-названием источника (например, Медуза, Важные истории, The Bell, BAZA, "
                    "РБК, Коммерсантъ), внутри блока — развёрнутые фактологичные описания новостей этого "
                    "источника буллетами. НЕ объединяй новости разных источников в общие тематические блоки "
                    "и не перемешивай их. В начале строкой \"Главное\" кратко перечисли 3-4 главные новости,"
                    "затем блоки по источникам. Не опускай важные подробности. Если каких-то деталей нет "
                    "в исходных постах — не додумывай."
                )},
                {"role": "user", "content": posts_text}
            ],
            "temperature": 0.4,
            "max_tokens": 800
        }).encode()
        req = urllib.request.Request(base_url.rstrip("/") + "/chat/completions", data=payload,
                                     headers={"Content-Type": "application/json",
                                              "Authorization": "Bearer " + api_key})
        with urllib.request.urlopen(req, timeout=60) as r:
            data = json.loads(r.read().decode())
        return data["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print("AI summarize error:", e)
        return None


def _collect_posts(hours: int) -> tuple:
    """Собирает все посты за `hours` часов; возвращает (сырой текст для ИИ, число постов)."""
    raw = []
    total = 0
    for ch in CHANNELS:
        posts = _channel(ch, hours=hours, limit=8)  # до 8 на канал — полнота для саммари
        label = {"meduzalive": "Медуза", "istories_media": "Важные истории",
                 "thebell_io": "The Bell", "bazabazon": "BAZA"}.get(ch, ch)
        for t, _d in posts:
            raw.append(f"[{label}] {t}")
            total += 1
    for name, url, lim in RSS_FEEDS:
        for t, _d in _rss(url, limit=lim, hours=hours):
            raw.append(f"[{name}] {t}")
            total += 1
    return "\n".join(raw), total


# ---------- Сборка ----------
def build(hours: int = None, use_ai: bool = True) -> str:
    """Собирает дайджест, сгруппированный СТРОГО ПО ИСТОЧНИКАМ (не по тематике).
    Каждый источник — отдельный блок с заголовком; внутри — посты этого источника.
    По умолчанию — за последние WINDOW_HOURS часов (2)."""
    import datetime as _dt
    hours = WINDOW_HOURS if hours is None else hours
    lines = [f"<b>📰 Дайджест за последние {hours} ч</b>", ""]
    emoji = {"meduzalive": "🟣", "istories_media": "🔵", "thebell_io": "🟠", "bazabazon": "⚫️"}
    total = 0

    # СБОР по источникам: (заголовок_блока, [(текст, время)])
    sources = []
    for ch in CHANNELS:
        label = {"meduzalive": "Медуза", "istories_media": "Важные истории",
                 "thebell_io": "The Bell", "bazabazon": "BAZA"}.get(ch, ch)
        posts = _channel(ch, hours=hours)
        if posts:
            sources.append((f"{emoji.get(ch, '•')} {label}", posts))
    for name, url, lim in RSS_FEEDS:
        posts = _rss(url, limit=lim, hours=hours)
        if posts:
            sources.append((f"📡 {name}", posts))

    if not sources:
        lines.append("За последние 2 часа свежих постов в каналах нет.")
        lines.append("")
    else:
        for title, posts in sources:
            lines.append(f"{title}")
            for t, _d in posts:
                lines.append(f"   • {t}")
                total += 1
            lines.append("")

    lines.append("━━━━━━━━━━━━━")
    lines.append(f"<b>💱 Курс (ЦБ):</b>")
    lines.append(f"{_curs()}")
    lines.append(f"⭐ Итого свежих постов: {total}")
    return "\n".join(lines)


def send(text: str) -> str:
    sys.path.insert(0, "/root/.openclaw/workspace/calendar")
    import bot_sender
    return bot_sender.send_text_to_owner(text)


if __name__ == "__main__":
    # --hours N — окно в часах (по умолчанию 2)
    hours = WINDOW_HOURS
    if "--hours" in sys.argv:
        try:
            hours = int(sys.argv[sys.argv.index("--hours") + 1])
        except Exception:
            pass
    txt = build(hours)
    if "--no-send" in sys.argv:
        print(txt)
    else:
        print(txt)
        print("---")
        print(send(txt))
