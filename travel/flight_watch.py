#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Мониторинг цен МСК → Канкун (туда-обратно) на декабрь 2026 / январь 2027.
Даты Дмитрия: вылет 25.12 (вечер, после 18:00) или 26.12; возврат в Москву — 10.01 вечером (край).
Источник: avticket.ru (статический HTML с ценами по месяцам).
Логика: парсит минимальные цены, ведёт историю, шлёт в Telegram владельцу,
если цена ≤ порога и улучшилась с прошлого запуска.

Cron: 0 6,18 * * * python3 /root/openclaw/travel/flight_watch.py >> /root/openclaw/travel/flight_watch.log 2>&1
"""

import json
import os
import re
import sys
import urllib.request
from datetime import datetime

URL = "https://avticket.ru/routes/mow/cun"
THRESHOLD_PER_PAX = 155000   # цель Дмитрия: ≤ 155 тыс ₽/чел туда-обратно
PASSENGERS = 2               # летят двое
THRESHOLD = THRESHOLD_PER_PAX * PASSENGERS  # 310 000 ₽ на двоих
STATE_FILE = "/root/openclaw/travel/flight_watch_state.json"
OWNER_CHAT_ID = "1916536646"
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

# Дополнительные источники (работают без API-ключа)
EXTRA_SOURCES = [
    ("tutu", "https://avia.tutu.ru/f/Moskva/Kankun/"),
    ("avianity", "https://avianity.ru/aviabilety/moskva-kankun"),
]

TARGET_MONTHS = {"Декабрь", "Январь"}


def fetch(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", "ignore")


def parse_extra(name, html):
    """Пытается вытащить минимальную цену туда-обратно из доп. источников."""
    if name == "tutu":
        m = re.search(r"от (\d[\d\s]{3,9}) руб", html)
        if m:
            return int(m.group(1).replace(" ", ""))
    if name == "avianity":
        # цены в таблице: [119 606](url) — пробелы обычные и неразрывные
        nums = []
        for x in re.findall(r"\[(\d{3}[\s\u00a0]?\d{3})\]\(", html):
            try:
                nums.append(int(x.replace("\u00a0", "").replace(" ", "")))
            except ValueError:
                pass
        # fallback: любые цены-кандидаты 50k-400k
        if not nums:
            for x in re.findall(r"(\d{3}[\s\u00a0]?\d{3})", html):
                try:
                    v = int(x.replace("\u00a0", "").replace(" ", ""))
                    if 50000 <= v <= 400000:
                        nums.append(v)
                except ValueError:
                    pass
        return min(nums) if nums else None


def parse(html):
    """Возвращает {Месяц: (цена_туда, цена_туда_обратно, даты)}"""
    out = {}
    blocks = re.findall(r'<div class="price-tickets-tr[^"]*">(.*?)</div>\s*</div>', html, re.S)
    for b in blocks:
        m = re.search(r"<strong>(\w+)</strong>", b)
        dates = re.findall(r'dsdsd">([\d.\- ]+)</span>', b)
        prices = re.findall(r'from-price-middle">([\d\s]+) ₽', b)
        if not m or not prices:
            continue
        month = m.group(1)
        p = [int(x.replace(" ", "")) for x in prices]
        one_way = p[0] if len(p) > 0 else None
        round_trip = p[1] if len(p) > 1 else None
        out[month] = {"one_way": one_way, "round_trip": round_trip,
                      "dates": dates[:2] if dates else []}
    return out


def load_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE) as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, ensure_ascii=False, indent=1)


def send_tg(text):
    """Отправка владельцу через бота (та же схема, что bot_sender.py)."""
    try:
        import subprocess
        r = subprocess.run(
            ["python3", "/root/openclaw/calendar/bot_sender.py", "send", "owner", text],
            capture_output=True, text=True, timeout=60)
        return r.stdout.strip() or r.stderr.strip()
    except Exception as e:
        return f"TG error: {e}"


def main():
    ts = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    try:
        html = fetch(URL)
        data = parse(html)
    except Exception as e:
        print(f"[{ts}] FETCH ERROR avticket: {e}")
        data = {}

    if not data:
        print(f"[{ts}] PARSE ERROR: no months found")
        sys.exit(1)

    state = load_state()
    prev = state.get("last", {})
    state["last"] = data
    state["checked_at"] = ts
    state["passengers"] = PASSENGERS
    save_state(state)

    lines = [f"[{ts}] Цены МСК↔Канкун туда-обратно на {PASSENGERS} чел. (avticket):"]
    for month in ("Ноябрь", "Декабрь", "Январь", "Февраль"):
        if month in data:
            d = data[month]
            rt = d["round_trip"]
            ow = d["one_way"]
            total2 = rt * PASSENGERS if rt else None
            mark = "  ← В ЛИМИТЕ" if total2 and total2 <= THRESHOLD else ""
            lines.append(f"  {month}: {rt:,} ₽/чел = {total2:,} ₽ на двоих{mark}")

    # Доп. источники
    for name, url in EXTRA_SOURCES:
        try:
            h = fetch(url)
            v = parse_extra(name, h)
            if v:
                lines.append(f"  [{name}] мин. туда-обратно ≈ {v:,} ₽")
        except Exception as e:
            lines.append(f"  [{name}] недоступен: {e}")

    print("\n".join(lines))

    # Уведомление: если цена на двоих ≤ порога и улучшилась (или первая проверка)
    for month in ("Декабрь", "Январь"):
        d = data.get(month)
        if not d or not d["round_trip"]:
            continue
        rt = d["round_trip"]
        total2 = rt * PASSENGERS
        prev_total2 = prev.get(month, {}).get("round_trip")
        prev_total2 = prev_total2 * PASSENGERS if prev_total2 else None
        improved = prev_total2 is None or total2 < prev_total2
        if total2 <= THRESHOLD and improved:
            msg = (
                f"✈️ {month}: билеты МСК→Канкун туда-обратно {rt:,} ₽/чел, "
                f"итого {total2:,} ₽ на двоих (≤ {THRESHOLD:,} ₽, цель достигнута)"
                + (f", было {prev_total2:,} ₽" if prev_total2 else "")
                + "\n\nПроверить на даты 25/26.12 → обратно 09.01\n"
                "(только рейсы с ≤1 пересадкой):\n"
                "• Turkish (Стамбул): https://www.turkishairlines.com/ru-ru/\n"
                "• Qatar (Доха): https://www.qatarairways.com/ru-ru/\n"
                "• Emirates (Дубай): https://www.emirates.com/ru/russian/\n"
                "Aviasales: https://www.aviasales.ru/search/MOW2512CUN0901?adults=2\n"
                "https://www.aviasales.ru/search/MOW2612CUN0901?adults=2"
            )
            res = send_tg(msg)
            print(f"[{ts}] NOTIFY {month}: {res}")
            state["notified"] = {month: total2}
            save_state(state)
        else:
            print(f"[{ts}] {month}: {total2:,} ₽ на двоих — уведомление не нужно "
                  f"(порог {THRESHOLD:,}, улучшение={improved})")


if __name__ == "__main__":
    main()
