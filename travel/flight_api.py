#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Поиск авиабилетов МСК→Канкун через Travelpayouts API (Aviasales).
Даты: вылет 25.12 или 26.12, обратно 09.01, 2 пассажира, ≤1 пересадка.
Маркер: /root/.openclaw/credentials/travelpayouts.key
Cron: 0 6,18 * * * python3 /root/openclaw/travel/flight_api.py >> /root/openclaw/travel/flight_api.log 2>&1
"""

import json
import os
import re
import subprocess
import sys
import urllib.parse
import urllib.request
from datetime import datetime

CRED = "/root/.openclaw/credentials/travelpayouts.key"
PAX = 2
MAX_STOPS = 1
OUTBOUND = ["2026-12-25", "2026-12-26"]
RETURN = "2027-01-09"
THRESHOLD = 310000  # на двоих
STATE_FILE = "/root/openclaw/travel/flight_api_state.json"


def read_key():
    if os.path.exists(CRED):
        return open(CRED).read().strip()
    return None


def api_prices(token, date):
    params = {
        "origin": "MOW", "destination": "CUN",
        "departure_at": date, "return_at": RETURN,
        "currency": "rub", "market": "ru",
        "limit": "30", "sorting": "price",
        "one_way": "false", "unique": "false",
        "token": token,
    }
    url = "https://api.travelpayouts.com/aviasales/v3/prices_for_dates?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())


def stops_from_link(link):
    """Пересадки считаем из цепочек аэропортов в t-параметре ссылки.
    Цепочка вида VKOISTCUN = 3 аэропорта = 1 пересадка. Считаем макс по направлениям."""
    t = re.search(r"t=([A-Za-z0-9_]+)", link or "")
    chain = t.group(1) if t else ""
    chains = re.findall(r"[A-Z]{6,}", chain)
    stops_per_dir = []
    for c in chains:
        n = len(c) // 3
        stops_per_dir.append(max(0, n - 2))
    if not stops_per_dir:
        return None
    return max(stops_per_dir)


def send_tg(text):
    r = subprocess.run(
        ["python3", "/root/openclaw/calendar/bot_sender.py", "send", "owner", text],
        capture_output=True, text=True, timeout=60)
    return r.stdout.strip() or r.stderr.strip()


def load_state():
    if os.path.exists(STATE_FILE):
        try:
            return json.load(open(STATE_FILE))
        except Exception:
            return {}
    return {}


def save_state(s):
    json.dump(s, open(STATE_FILE, "w"), ensure_ascii=False, indent=1)


def main():
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    token = read_key()
    if not token:
        print(f"[{ts}] Нет маркера в {CRED}")
        sys.exit(2)

    results = []
    for date in OUTBOUND:
        try:
            d = api_prices(token, date)
            if not d.get("success"):
                print(f"[{ts}] API error {date}: {d}")
                continue
            for it in d.get("data", []):
                price = it.get("price")
                if not price:
                    continue
                stops = stops_from_link(it.get("link"))
                results.append({
                    "date": date, "price": price,
                    "stops": stops,
                    "airline": it.get("airline"),
                    "dep": it.get("departure_at", "")[:16],
                    "ret": it.get("return_at", "")[:16],
                    "link": it.get("link", ""),
                })
        except Exception as e:
            print(f"[{ts}] fetch error {date}: {e}")

    if not results:
        print(f"[{ts}] Пусто")
        sys.exit(1)

    # фильтр ≤1 пересадка (где пересадки известны)
    filtered = [r for r in results if r["stops"] is None or r["stops"] <= MAX_STOPS]
    filtered.sort(key=lambda r: r["price"])
    best = filtered[:10] if filtered else results[:10]

    lines = [f"[{ts}] МСК→Канкун на {PAX} чел. (API Travelpayouts), ≤{MAX_STOPS} пересадка:"]
    for r in best[:10]:
        total2 = r["price"] * PAX
        mark = " ← В ЛИМИТЕ" if total2 <= THRESHOLD else ""
        lines.append(
            f"  {r['date']}: {r['price']:,} ₽/чел = {total2:,} ₽ на двоих | "
            f"пересадок {r['stops']} | {r['airline']} | {r['dep'][:16]}{mark}")
    print("\n".join(lines))

    # уведомление при улучшении
    state = load_state()
    prev_best = state.get("best_price")
    state["last_check"] = ts
    save_state(state)

    if best and best[0]["stops"] is not None and best[0]["stops"] <= MAX_STOPS:
        b = best[0]
        total2 = b["price"] * PAX
        if total2 <= THRESHOLD and (prev_best is None or total2 < prev_best):
            msg = (
                f"✈️ Найдено: МСК→Канкун {b['date']} → 09.01, "
                f"{b['price']:,} ₽/чел = {total2:,} ₽ на двоих\n"
                f"Авиакомпания {b['airline']}, пересадок {b['stops']}\n"
                f"Вылет {b['dep']}, возврат {b['ret']}\n\n"
                f"Ссылка: https://www.aviasales.ru{b['link']}"
            )
            res = send_tg(msg)
            print(f"[{ts}] NOTIFY: {res}")
            state["best_price"] = total2
            save_state(state)


if __name__ == "__main__":
    main()
