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

SOCKS = "socks5h://127.0.0.1:10808"
CHANNELS = ["meduzalive", "istories_media", "thebell_io", "bazabazon"]
OWNER = "1916536646"

# Окно времени для "дайджеста за последние N часов" (по умолчанию 2)
WINDOW_HOURS = 2

# Постов на канал (увеличено: объём +50%, было по 2)
POSTS_PER_CHANNEL = 3
# Максимум символов на пост (обрезка) — увеличен для полноты текста
MAX_POST_LEN = 280


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
        r = subprocess.run(
            ["curl", "-s", "--max-time", "20", "--socks5-hostname", SOCKS,
             "-A", "Mozilla/5.0", f"https://t.me/s/{ch}"],
            capture_output=True, text=True)
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
        base_url = keys.get("baseUrl", "https://api.deepseek.com/v1")
        if not api_key:
            return None
        payload = json.dumps({
            "model": "deepseek-chat",
            "messages": [
                {"role": "system", "content": (
                    "Ты — редактор новостного дайджеста. Из списка сырых постов за последние 2 часа "
                    "составь компактное, ясное саммари на русском. Выдели главные темы, сгруппируй "
                    "похожие новости, убери повторы и служебный мусор. Формат: короткие абзацы и "
                    "буллеты, в начале заголовок \"Главное за 2 часа\". Без лишних слов."
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
    return "\n".join(raw), total


# ---------- Сборка ----------
def build(hours: int = None, use_ai: bool = True) -> str:
    """Собирает дайджест. По умолчанию — за последние WINDOW_HOURS часов (2).
    Увеличенный объём (+50%: по 3 поста на канал вместо 2) и улучшенная подача."""
    import datetime as _dt
    hours = WINDOW_HOURS if hours is None else hours
    lines = [f"<b>📰 Дайджест за последние {hours} ч</b>", ""]
    # эмодзи-маркеры для каналов
    emoji = {"meduzalive": "🟣", "istories_media": "🔵", "thebell_io": "🟠", "bazabazon": "⚫️"}
    total = 0

    if use_ai:
        raw, total = _collect_posts(hours)
        summ = _ai_summarize(raw) if raw else None
        if summ:
            lines.append(summ)
            lines.append("")
            lines.append("━━━━━━━━━━━━━")
            lines.append(f"<b>💱 Курс (ЦБ):</b>")
            lines.append(f"{_curs()}")
            lines.append(f"⭐ Свежих постов за {hours} ч: {total}")
            return "\n".join(lines)
        # если ИИ не сработал — fallback на сырой список

    for ch in CHANNELS:
        posts = _channel(ch, hours=hours)
        if not posts:
            continue
        label = {"meduzalive": "Медуза", "istories_media": "Важные истории",
                 "thebell_io": "The Bell", "bazabazon": "BAZA"}.get(ch, ch)
        lines.append(f"{emoji.get(ch, '•')} <b>{label}</b>")
        for t, _d in posts:
            lines.append(f"   • {t}")
            total += 1
        lines.append("")
    if total == 0:
        lines.append("За последние 2 часа свежих постов в каналах нет.")
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
