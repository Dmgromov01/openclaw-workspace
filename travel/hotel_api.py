#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Поиск отелей: Amadeus (мир) + Яндекс Путешествия (РФ).
Аналог flight_api.py для гостиниц.

Ключи:
  Amadeus: /root/.openclaw/credentials/amadeus.json  {"client_id": "...", "client_secret": "..."}
  Яндекс:  /root/.openclaw/credentials/yandex-travel.key  (OAuth-токен партнёрской сети Путешествий)

Примеры:
  python3 hotel_api.py --provider amadeus --city CUN --in 2026-12-25 --out 2027-01-09
  python3 hotel_api.py --provider yandex --city Москва --in 2026-12-25 --out 2027-01-09
  python3 hotel_api.py --provider yandex --city Москва --in 2026-12-25 --out 2027-01-09 --threshold 15000
"""

import argparse
import json
import os
import subprocess
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime

BASE = "/root/.openclaw/credentials"
AMADEUS_TOKEN_URL = "https://test.api.amadeus.com/v1/security/oauth2/token"
AMADEUS_HOTEL_LIST = "https://test.api.amadeus.com/v1/reference-data/locations/hotels/by-city"
AMADEUS_OFFERS = "https://test.api.amadeus.com/v3/shopping/hotel-offers"
YANDEX_BASE = "https://whitelabel.travel.yandex-net.ru"


def load_json(path):
    if os.path.exists(path):
        try:
            return json.load(open(path))
        except Exception:
            return {}
    return {}


def read_file(path):
    if os.path.exists(path):
        return open(path).read().strip()
    return None


def http_get(url, headers=None, timeout=30):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0", **(headers or {})})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.status, json.loads(r.read().decode())


def http_post(url, data, headers=None, timeout=30):
    body = urllib.parse.urlencode(data).encode()
    req = urllib.request.Request(url, data=body, headers={"User-Agent": "Mozilla/5.0", **(headers or {})})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.status, json.loads(r.read().decode())


# ---------- Amadeus ----------

def amadeus_token(cfg):
    s, d = http_post(AMADEUS_TOKEN_URL, {
        "grant_type": "client_credentials",
        "client_id": cfg["client_id"],
        "client_secret": cfg["client_secret"],
    }, headers={"Content-Type": "application/x-www-form-urlencoded"})
    if s != 200:
        raise RuntimeError(f"Amadeus token: HTTP {s} {d}")
    return d["access_token"]


def amadeus_search(cfg, city_iata, check_in, check_out, adults=2):
    tok = amadeus_token(cfg)
    auth = {"Authorization": f"Bearer {tok}"}

    # 1) список отелей города (до 40)
    s, d = http_get(AMADEUS_HOTEL_LIST + "?" + urllib.parse.urlencode({
        "cityCode": city_iata, "radius": 50, "radiusUnit": "KM", "page[limit]": 40,
    }), headers=auth)
    if s != 200:
        raise RuntimeError(f"Amadeus hotel list: HTTP {s} {d}")
    hotels = d.get("data", [])
    if not hotels:
        return []
    hotel_ids = ",".join(h["hotelId"] for h in hotels[:20])  # до 20 за запрос

    # 2) предложения по отелям на даты
    s, d = http_get(AMADEUS_OFFERS + "?" + urllib.parse.urlencode({
        "hotelIds": hotel_ids, "adults": adults,
        "checkInDate": check_in, "checkOutDate": check_out,
        "currency": "RUB", "bestRateOnly": "true",
    }), headers=auth)
    if s != 200:
        raise RuntimeError(f"Amadeus offers: HTTP {s} {d}")

    results = []
    for h in d.get("data", []):
        hid = h.get("hotel", {}).get("hotelId")
        name = h.get("hotel", {}).get("name", "")
        offers = h.get("offers", [])
        for off in offers:
            price = off.get("price", {})
            total = price.get("total")
            if not total:
                continue
            results.append({
                "source": "amadeus",
                "hotel": name,
                "price_total": float(total),
                "currency": price.get("currency", "RUB"),
                "board": off.get("boardType", ""),
                "nights": off.get("room", {}).get("typeEstimated", {}).get("category", ""),
                "link": f"https://amadeus.com/hotel/{hid}",
            })
    return results


# ---------- Яндекс Путешествия ----------

def yandex_search(token, query, check_in, check_out, adults=2):
    auth = {"Authorization": "OAuth " + token}

    # 1) suggest: ищем регион/отель по запросу
    s, d = http_get(YANDEX_BASE + "/hotels/suggest?" + urllib.parse.urlencode({
        "query": query, "lang": "ru",
    }), headers=auth)
    if s != 200:
        raise RuntimeError(f"Yandex suggest: HTTP {s} {d}")

    # ищем регион с типом region (у него есть region_id)
    candidates = d.get("results", {}).get("regions", []) or d.get("results", {}).get("locations", [])
    region_id = None
    for c in candidates:
        if c.get("type") in ("region", "location") or c.get("regionId"):
            region_id = c.get("regionId") or c.get("id")
            break
    if not region_id and candidates:
        region_id = candidates[0].get("regionId") or candidates[0].get("id")
    if not region_id:
        return [], d

    # 2) search: сниппеты отелей с ценами
    s, d2 = http_get(YANDEX_BASE + "/hotels/search?" + urllib.parse.urlencode({
        "region_id": region_id,
        "check_in_date": check_in, "check_out_date": check_out,
        "adults": adults, "lang": "ru", "currency": "RUB",
    }), headers=auth)
    if s != 200:
        raise RuntimeError(f"Yandex search: HTTP {s} {d2}")

    results = []
    for h in d2.get("results", {}).get("hotels", []):
        name = h.get("name", "")
        price = h.get("price") or h.get("minPrice") or {}
        total = price.get("total") or price.get("value")
        if not total:
            continue
        results.append({
            "source": "yandex",
            "hotel": name,
            "price_total": float(total),
            "currency": price.get("currency", "RUB"),
            "board": h.get("boardType", ""),
            "nights": h.get("category", ""),
            "link": h.get("url", ""),
        })
    return results, d2


# ---------- общее ----------

def send_tg(text):
    r = subprocess.run(
        ["python3", "/root/openclaw/calendar/bot_sender.py", "send", "owner", text],
        capture_output=True, text=True, timeout=60)
    return r.stdout.strip() or r.stderr.strip()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--provider", choices=["amadeus", "yandex"], required=True)
    ap.add_argument("--city", required=True, help="IATA (amadeus, напр. CUN) или название (yandex, напр. Москва)")
    ap.add_argument("--in", dest="check_in", required=True)
    ap.add_argument("--out", dest="check_out", required=True)
    ap.add_argument("--adults", type=int, default=2)
    ap.add_argument("--threshold", type=float, default=0, help="порог для уведомления в TG")
    ap.add_argument("--top", type=int, default=10)
    args = ap.parse_args()

    if args.provider == "amadeus":
        cfg = load_json(f"{BASE}/amadeus.json")
        if not cfg.get("client_id"):
            print("Нет ключа Amadeus: создай app на developers.amadeus.com и сохрани в", f"{BASE}/amadeus.json")
            sys.exit(2)
        results = amadeus_search(cfg, args.city.upper(), args.check_in, args.check_out, args.adults)
    else:
        token = read_file(f"{BASE}/yandex-travel.key")
        if not token:
            print("Нет OAuth-токена Яндекса в", f"{BASE}/yandex-travel.key")
            sys.exit(2)
        results, _ = yandex_search(token, args.city, args.check_in, args.check_out, args.adults)

    results.sort(key=lambda r: r["price_total"])
    best = results[: args.top]

    print(f"[{datetime.now():%Y-%m-%d %H:%M:%S}] Отели {args.city} {args.check_in}→{args.check_out} "
          f"({args.adults} взр.) через {args.provider}:")
    for r in best:
        mark = " ← в лимите" if args.threshold and r["price_total"] <= args.threshold else ""
        print(f"  {r['price_total']:,.0f} {r['currency']} | {r['hotel'][:60]} | {r['board'] or '—'}{mark}")

    if not best:
        sys.exit(1)


if __name__ == "__main__":
    main()
