#!/usr/bin/env python3
"""
MiniApp Personal Hub — сервер: статика + API.
- GET  /                    → static/index.html
- GET  /api/digest          → {blocks:[{title,posts}], curs, total, ts}
- GET  /api/sources         → [{id,type,name,title}]
- POST /api/sources         → добавить {type,name,title}
- DELETE /api/sources?id=N  → удалить
Источники хранятся в sources.json (рядом со скриптом).
Дайджест собирается из этих источников (без AI-саммари — быстро и надёжно).
"""
import json
import os
import sys
import time
import threading
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

BASE = os.path.dirname(os.path.abspath(__file__))
STATIC = os.path.join(BASE, "static")
SOURCES_FILE = os.path.join(BASE, "sources.json")
CACHE_TTL = 900  # 15 минут

sys.path.insert(0, "/root/openclaw/calendar")
import digest  # переиспользуем парсеры каналов/RSS и курс ЦБ

# ---------- Google Calendar (OAuth, чтение) ----------
GCAL_DIR = "/root/.openclaw/credentials/gcal"
CAL_ID = "dmgromov03@gmail.com"
CAL_TZ = ZoneInfo("Europe/Moscow")
CAL_CACHE = {"ts": 0.0, "data": None}


def get_calendar_service():
    """Собирает сервис Google Calendar из OAuth-токенов (oauth-client.json + tokens.json)."""
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build

    tok = json.load(open(os.path.join(GCAL_DIR, "tokens.json")))
    cli = json.load(open(os.path.join(GCAL_DIR, "oauth-client.json")))['web']
    creds = Credentials(
        token=tok.get('access_token'),
        refresh_token=tok.get('refresh_token'),
        token_uri=cli['token_uri'],
        client_id=cli['client_id'],
        client_secret=cli['client_secret'],
        scopes=[tok.get('scope')],
    )
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
    return build("calendar", "v3", credentials=creds)


def build_calendar_json(days=7):
    """События на N дней: [{date, dow, events:[{time, summary, location, durMin}]}]."""
    svc = get_calendar_service()
    now = datetime.now(CAL_TZ)
    start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end = start + timedelta(days=days)
    r = svc.events().list(
        calendarId=CAL_ID,
        timeMin=start.isoformat(),
        timeMax=end.isoformat(),
        singleEvents=True,
        orderBy="startTime",
        maxResults=100,
    ).execute()
    items = r.get("items", [])
    WEEKDAYS = ["пн", "вт", "ср", "чт", "пт", "сб", "вс"]
    MONTHS = ["янв", "фев", "мар", "апр", "май", "июн",
              "июл", "авг", "сен", "окт", "ноя", "дек"]
    byday = {}
    for e in items:
        s = e["start"].get("dateTime")
        if not s:
            continue
        dt = datetime.fromisoformat(s)
        key = dt.date().isoformat()
        dur = None
        ed = e["end"].get("dateTime")
        if ed:
            try:
                dur = int((datetime.fromisoformat(ed) - dt).total_seconds() // 60)
            except Exception:
                dur = None
        byday.setdefault(key, []).append({
            "time": dt.strftime("%H:%M"),
            "summary": e.get("summary", "(без названия)"),
            "location": e.get("location"),
            "durMin": dur,
        })
    out = []
    cur = start.date()
    for i in range(days):
        d = cur + timedelta(days=i)
        label = f"{WEEKDAYS[d.weekday()]} {d.day} {MONTHS[d.month - 1]}"
        if i == 0:
            label += " (сегодня)"
        out.append({"date": d.isoformat(), "label": label, "events": byday.get(d.isoformat(), [])})
    return {"days": out, "ts": int(time.time())}

DEFAULT_SOURCES = [
    {"id": 1, "type": "TG", "name": "meduzalive", "title": "Медуза"},
    {"id": 2, "type": "TG", "name": "istories_media", "title": "Важные истории"},
    {"id": 3, "type": "TG", "name": "thebell_io", "title": "The Bell"},
    {"id": 4, "type": "TG", "name": "bazabazon", "title": "BAZA"},
    {"id": 5, "type": "RSS", "name": "https://rssexport.rbc.ru/rbcnews/news/30/full.rss", "title": "РБК"},
    {"id": 6, "type": "RSS", "name": "https://www.kommersant.ru/rss/news.xml", "title": "Коммерсантъ"},
]

DIGEST_CACHE = {"ts": 0.0, "data": None}
CACHE_LOCK = threading.Lock()


def load_sources():
    if os.path.exists(SOURCES_FILE):
        try:
            with open(SOURCES_FILE, encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list) and data:
                return data
        except Exception:
            pass
    return list(DEFAULT_SOURCES)


def save_sources(sources):
    with open(SOURCES_FILE, "w", encoding="utf-8") as f:
        json.dump(sources, f, ensure_ascii=False, indent=2)


def collect_digest(sources, hours=24):
    """Собирает посты по источникам из sources.json; возвращает (blocks, total)."""
    emoji = {"TG": "🟣", "RSS": "📡"}
    blocks = []
    total = 0
    for src in sources:
        try:
            if src.get("type") == "TG":
                ch = src["name"].lstrip("@")
                posts = digest._channel(ch, hours=hours, limit=6)
                label = src.get("title") or ch
            else:
                url = src["name"]
                posts = digest._rss(url, limit=10, hours=hours)
                label = src.get("title") or url
        except Exception:
            continue
        texts = [t for t, _d in posts]
        if texts:
            blocks.append({"title": f"{emoji.get(src.get('type'), '•')} {label}", "posts": texts})
            total += len(texts)
    return blocks, total


def build_digest_json():
    sources = load_sources()
    blocks, total = collect_digest(sources)
    try:
        curs = digest._curs()
    except Exception:
        curs = "курс недоступен"
    return {"blocks": blocks, "curs": curs, "total": total, "ts": int(time.time())}


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=STATIC, **kwargs)

    # ---------- helpers ----------
    def _send_json(self, obj, code=200):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    # ---------- routes ----------
    def do_GET(self):
        p = urlparse(self.path)
        if p.path == "/api/digest":
            now = time.time()
            with CACHE_LOCK:
                if DIGEST_CACHE["data"] is None or now - DIGEST_CACHE["ts"] > CACHE_TTL:
                    DIGEST_CACHE["data"] = build_digest_json()
                    DIGEST_CACHE["ts"] = now
                data = DIGEST_CACHE["data"]
            return self._send_json(data)
        if p.path == "/api/sources":
            return self._send_json({"sources": load_sources()})
        if p.path == "/api/calendar":
            now = time.time()
            with CACHE_LOCK:
                if CAL_CACHE["data"] is None or now - CAL_CACHE["ts"] > 300:
                    try:
                        CAL_CACHE["data"] = build_calendar_json(days=7)
                        CAL_CACHE["ts"] = now
                    except Exception as ex:
                        return self._send_json({"error": str(ex), "days": []}, 500)
                data = CAL_CACHE["data"]
            return self._send_json(data)
        return super().do_GET()

    def do_POST(self):
        p = urlparse(self.path)
        if p.path == "/api/sources":
            try:
                length = int(self.headers.get("Content-Length", 0))
                body = json.loads(self.rfile.read(length) or b"{}")
            except Exception:
                return self._send_json({"error": "bad json"}, 400)
            name = (body.get("name") or "").strip()
            if not name:
                return self._send_json({"error": "name required"}, 400)
            sources = load_sources()
            new_id = max([s["id"] for s in sources], default=0) + 1
            sources.append({
                "id": new_id,
                "type": "RSS" if body.get("type") == "RSS" else "TG",
                "name": name,
                "title": (body.get("title") or name).strip(),
            })
            save_sources(sources)
            DIGEST_CACHE["ts"] = 0  # сброс кеша дайджеста
            return self._send_json({"ok": True, "sources": sources})
        return self._send_json({"error": "not found"}, 404)

    def do_DELETE(self):
        p = urlparse(self.path)
        if p.path == "/api/sources":
            q = parse_qs(p.query)
            try:
                sid = int(q.get("id", ["0"])[0])
            except Exception:
                return self._send_json({"error": "bad id"}, 400)
            sources = [s for s in load_sources() if s["id"] != sid]
            save_sources(sources)
            DIGEST_CACHE["ts"] = 0
            return self._send_json({"ok": True, "sources": sources})
        return self._send_json({"error": "not found"}, 404)

    def log_message(self, fmt, *args):
        sys.stderr.write("[miniapp] %s - %s\n" % (self.address_string(), fmt % args))


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
    server = HTTPServer(("0.0.0.0", port), Handler)
    print(f"MiniApp server on :{port} (static: {STATIC})", flush=True)
    server.serve_forever()
