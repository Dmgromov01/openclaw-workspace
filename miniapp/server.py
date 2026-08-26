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
import hashlib
import threading
import urllib.request
import urllib.parse
import html
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

BASE = os.path.dirname(os.path.abspath(__file__))
STATIC = os.environ.get("MINIAPP_STATIC", os.path.join(BASE, "static"))
SOURCES_FILE = os.environ.get("MINIAPP_SOURCES", os.path.join(BASE, "sources.json"))
CACHE_TTL = 900  # 15 минут

# AI через OpenClaw gateway (OpenAI-совместимый), НЕ напрямую в DeepSeek.
# Значения берутся из env или .env (systemd env не прокидывает .env напрямую).
def _read_env_file():
    """Читает .env в dict (значения не логируем)."""
    env = os.environ.get("MINIAPP_ENV", "/root/.openclaw/.env")
    vals = {}
    if os.path.exists(env):
        for line in open(env, encoding="utf-8"):
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                vals[k.strip()] = v.strip().strip('"').strip("'")
    return vals

_env_vals = _read_env_file()
GATEWAY_URL = (os.environ.get("OPENCLAW_GATEWAY_URL") or _env_vals.get("OPENCLAW_GATEWAY_URL") or "http://127.0.0.1:18789").rstrip("/")
GATEWAY_TOKEN = os.environ.get("OPENCLAW_GATEWAY_TOKEN") or _env_vals.get("OPENCLAW_GATEWAY_TOKEN") or ""
MAX_SOURCES = 12  # лимит источников (SKILL.md: только https, без внутренних IP)

sys.path.insert(0, os.environ.get("OPENCLAW_CALENDAR_DIR", "/root/openclaw/calendar"))
import digest  # переиспользуем парсеры каналов/RSS и курс ЦБ

# ---------- Auth (Telegram WebApp initData + пользователи) ----------
sys.path.insert(0, BASE)
import auth as miniapp_auth

# ---------- Google Calendar (OAuth, чтение) ----------
GCAL_DIR = os.environ.get("MINIAPP_GCAL_DIR", "/root/.openclaw/credentials/gcal")
CAL_ID = os.environ.get("MINIAPP_CAL_ID", "dmgromov03@gmail.com")
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

def _proxy_json(url, timeout=12):
    """GET внешнего http API → (dict, None) или (None, err)."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "PersonalHub/1.0"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8", "replace")), None
    except Exception as ex:
        return None, str(ex)


def _is_private_host(host):
    """SSRF-защита: True, если host — localhost/private/reserved IP или не резолвится."""
    import ipaddress
    import socket
    try:
        infos = socket.getaddrinfo(host, None)
    except Exception:
        return True
    for info in infos:
        ip = info[4][0]
        try:
            a = ipaddress.ip_address(ip.split("%")[0])
        except Exception:
            return True
        if a.is_private or a.is_loopback or a.is_link_local or a.is_reserved or a.is_multicast or a.is_unspecified:
            return True
    return False


def _validate_source_url(url):
    """SSRF: RSS только https, не private IP. Возвращает (ok, err)."""
    if not url.startswith("https://"):
        return False, "RSS должен быть https://"
    from urllib.parse import urlparse
    host = urlparse(url).hostname or ""
    if not host:
        return False, "Некорректный URL"
    if _is_private_host(host):
        return False, "URL ведёт на внутренний адрес"
    return True, None


def _summarize_via_gateway(name, posts_text):
    """AI-саммари через OpenClaw gateway (не DeepSeek напрямую). Возвращает текст или None."""
    if not GATEWAY_TOKEN or not posts_text:
        return None
    joined = "\n".join(posts_text[:12])
    prompt = (
        f"Сделай краткое связное саммари новостей из источника «{name}» на русском. "
        "Сохрани ключевые факты и цифры, не искажай смысл, не выдумывай. "
        "Если новостей нет — напиши «—».\n\nНовости:\n" + joined[:12000]
    )
    body = json.dumps({
        "model": "deepseek/deepseek-v4-flash",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 800,
        "temperature": 0.3,
    }).encode()
    req = urllib.request.Request(
        GATEWAY_URL + "/v1/chat/completions",
        data=body,
        headers={
            "Content-Type": "application/json",
            "Authorization": "Bearer " + GATEWAY_TOKEN,
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=90) as r:
            d = json.loads(r.read().decode("utf-8", "replace"))
        return (d.get("choices") or [{}])[0].get("message", {}).get("content") or None
    except Exception as ex:
        sys.stderr.write("[miniapp] gateway summarize error: %s\n" % ex)
        return None


DEFAULT_SOURCES = [
    {"id": 1, "type": "TG", "name": "meduzalive", "title": "Медуза"},
    {"id": 2, "type": "TG", "name": "istories_media", "title": "Важные истории"},
    {"id": 3, "type": "TG", "name": "thebell_io", "title": "The Bell"},
    {"id": 4, "type": "TG", "name": "bazabazon", "title": "BAZA"},
    {"id": 5, "type": "RSS", "name": "https://rssexport.rbc.ru/rbcnews/news/30/full.rss", "title": "РБК"},
    {"id": 6, "type": "RSS", "name": "https://www.kommersant.ru/rss/news.xml", "title": "Коммерсантъ"},
]

# MyMemory API: бесплатный перевод без ключа. С email-параметром (de=) лимит 50K симв./день вместо 5K.
# Email НЕ светится в клиенте — проксируется только нашим сервером.
MYMEMORY_EMAIL = os.environ.get("MYMEMORY_EMAIL", "dmgromov03@gmail.com")
MYMEMORY_MAX_CHARS = 2000  # жёсткий лимит на запрос (MyMemory: аноним 500, с email больше)


class MyMemoryError(Exception):
    pass


def translate_mymemory(text: str, lang_from: str, lang_to: str) -> dict:
    """Прокси к MyMemory: возвращает {ok, text, match, source} или бросает MyMemoryError."""
    q = urllib.parse.quote(text)
    url = (f"https://api.mymemory.translated.net/get?q={q}"
           f"&langpair={lang_from}|{lang_to}&de={MYMEMORY_EMAIL}")
    data, err = _proxy_json(url)
    if err:
        raise MyMemoryError(err)
    if data.get("responseStatus") != 200:
        raise MyMemoryError(data.get("responseDetails") or "translate failed")
    rd = data.get("responseData") or {}
    return {
        "ok": True,
        "text": rd.get("translatedText") or "",
        "match": rd.get("match", 1),
    }


DIGEST_CACHE = {"ts": 0.0, "data": None}
CAL_CACHE = {"ts": 0.0, "data": None}
CACHE_LOCK = threading.Lock()


def _refresh_digest_cache(force=False):
    """Обновляет кеш дайджеста (сеть/AI — ВНЕ блокировки). Возвращает данные или None."""
    try:
        data = build_digest_json()
    except Exception as ex:
        sys.stderr.write("[miniapp] digest refresh error: %s\n" % ex)
        return None
    with CACHE_LOCK:
        DIGEST_CACHE["data"] = data
        DIGEST_CACHE["ts"] = time.time()
    return data


def _refresh_calendar_cache():
    """Обновляет кеш календаря (вне блокировки)."""
    try:
        data = build_calendar_json(days=7)
    except Exception as ex:
        sys.stderr.write("[miniapp] calendar refresh error: %s\n" % ex)
        return None
    with CACHE_LOCK:
        CAL_CACHE["data"] = data
        CAL_CACHE["ts"] = time.time()
    return data


def _cache_worker():
    """Фоновый поток: держит кеши тёплыми (stale-while-revalidate), не блокируя HTTP."""
    while True:
        try:
            now = time.time()
            with CACHE_LOCK:
                need_digest = DIGEST_CACHE["data"] is None or now - DIGEST_CACHE["ts"] > CACHE_TTL
                need_cal = CAL_CACHE["data"] is None or now - CAL_CACHE["ts"] > 300
            if need_digest:
                _refresh_digest_cache()
            if need_cal:
                _refresh_calendar_cache()
        except Exception as ex:
            sys.stderr.write("[miniapp] cache worker error: %s\n" % ex)
        time.sleep(60)


def start_cache_worker():
    t = threading.Thread(target=_cache_worker, daemon=True)
    t.start()
    return t


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
    blocks = []
    total = 0
    for s in sources:
        try:
            if s.get("type") == "TG":
                ch = s["name"].lstrip("@")
                posts = digest._channel(ch, hours=hours, limit=6)
                label = s.get("title") or ch
            else:
                url = s["name"]
                posts = digest._rss(url, limit=10, hours=hours)
                label = s.get("title") or url
        except Exception:
            continue
        texts = [t for t, _d in posts]
        if texts:
            blocks.append({"title": label, "type": s.get("type"), "posts": texts})
            total += len(texts)
    return blocks, total


def build_digest_json(use_ai=True):
    """Собирает дайджест; каждый блок — источник с AI-саммари (через OpenClaw gateway) + сырые посты."""
    sources = load_sources()
    blocks, total = collect_digest(sources, hours=3)
    if use_ai:
        for b in blocks:
            try:
                summ = _summarize_via_gateway(b["title"], b["posts"])
                if summ:
                    b["summary"] = summ
            except Exception:
                pass
    try:
        curs = digest._curs()
    except Exception:
        curs = "курс недоступен"
    return {"blocks": blocks, "curs": curs, "total": total, "ts": int(time.time())}


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=STATIC, **kwargs)

    def _norm_path(self, path):
        """Снимает префикс /miniapp, чтобы API работал и напрямую, и за nginx."""
        if path.startswith("/miniapp/"):
            return path[len("/miniapp"):]
        return path

    # ---------- helpers ----------
    def _send_json(self, obj, code=200):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _auth_user(self):
        """Токен из Authorization: Bearer <token> → строка пользователя или None."""
        h = self.headers.get("Authorization", "")
        if not h.startswith("Bearer "):
            return None
        return miniapp_auth.auth(h[7:].strip())

    def _require_auth(self):
        """401, если нет валидного токена. Возвращает пользователя или None (ответ уже отправлен)."""
        user = self._auth_user()
        if user is None:
            self._send_json({"error": "unauthorized"}, 401)
            return None
        return user

    def _require_admin(self):
        user = self._require_auth()
        if user is None:
            return None
        if user["role"] != "admin":
            self._send_json({"error": "forbidden"}, 403)
            return None
        return user

    # ---------- routes ----------
    def do_GET(self):
        p = urlparse(self.path)
        p = p._replace(path=self._norm_path(p.path))
        if p.path in ("/", "/index.html"):
            # index.html отдаём с no-cache, чтобы Telegram WebView не держал старую версию
            try:
                with open(os.path.join(STATIC, "index.html"), "rb") as f:
                    body = f.read()
            except Exception:
                return self._send_json({"error": "no index"}, 500)
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store, no-cache, must-revalidate")
            self.send_header("Pragma", "no-cache")
            self.end_headers()
            self.wfile.write(body)
            return
        if p.path == "/api/bootstrap":
            """Единый эндпоинт старта: user + sources + calendar + digest + curs одним ответом."""
            user = self._require_auth()
            if user is None:
                return
            out = {"ok": True, "user": {
                "id": user["id"], "telegram_id": user["telegram_id"],
                "username": user["username"], "first_name": user["first_name"],
                "role": user["role"], "allowed": bool(user["allowed"]),
            }}
            try:
                out["sources"] = load_sources()
            except Exception:
                out["sources"] = []
            with CACHE_LOCK:
                d = DIGEST_CACHE["data"]
                c = CAL_CACHE["data"]
            out["digest"] = d
            out["calendar"] = c
            return self._send_json(out)
        if p.path == "/api/auth/me":
            user = self._require_auth()
            if user is None:
                return
            return self._send_json({"ok": True, "user": {
                "id": user["id"], "telegram_id": user["telegram_id"],
                "username": user["username"], "first_name": user["first_name"],
                "role": user["role"], "allowed": bool(user["allowed"]),
            }})
        if p.path == "/api/admin/users":
            user = self._require_admin()
            if user is None:
                return
            return self._send_json({"ok": True, "users": miniapp_auth.list_users()})
        if p.path == "/api/admin/audit":
            user = self._require_admin()
            if user is None:
                return
            return self._send_json({"ok": True, "audit": miniapp_auth.audit(limit=50)})
        if p.path == "/api/digest":
            if self._require_auth() is None:
                return
            with CACHE_LOCK:
                data = DIGEST_CACHE["data"]
                ts = DIGEST_CACHE["ts"]
            if data is None:
                data = _refresh_digest_cache()
                if data is None:
                    return self._send_json({"error": "digest unavailable"}, 502)
            return self._send_json(data)
        if p.path == "/api/sources":
            if self._require_auth() is None:
                return
            return self._send_json({"sources": load_sources()})
        if p.path == "/api/calendar":
            if self._require_auth() is None:
                return
            with CACHE_LOCK:
                data = CAL_CACHE["data"]
            if data is None:
                data = _refresh_calendar_cache()
                if data is None:
                    return self._send_json({"error": "calendar unavailable", "days": []}, 502)
            return self._send_json(data)
        if p.path == "/api/keys":
            # BYOK: список ключей (только id/name/tail — без значений)
            user = self._require_auth()
            if user is None:
                return
            return self._send_json({"ok": True, "keys": miniapp_auth.list_api_keys(user["telegram_id"])})
        if p.path == "/api/quiz":
            # Прокси к Open Trivia DB (https) — jservice.io мёртв с 2022
            if self._require_auth() is None:
                return
            q = parse_qs(p.query)
            count = q.get("count", ["1"])[0]
            data, err = _proxy_json("https://opentdb.com/api.php?amount=" + count)
            if err:
                return self._send_json({"error": err}, 502)
            clues = []
            for r in data.get("results", []):
                clues.append({
                    "question": html.unescape(r.get("question", "")),
                    "answer": html.unescape(r.get("correct_answer", "")),
                    "category": {"title": html.unescape(r.get("category", ""))},
                    "value": None,
                    "difficulty": r.get("difficulty"),
                    "airdate": None,
                })
            return self._send_json({"ok": True, "clues": clues})
        if p.path == "/api/activity":
            # Прокси к BoredAPI (форк Le Wagon) — boredapi.com мёртв
            if self._require_auth() is None:
                return
            q = parse_qs(p.query)
            params = []
            for k in ("type", "participants", "price", "minprice", "maxprice",
                      "minaccessibility", "maxaccessibility"):
                if k in q:
                    params.append(f"{k}={q[k][0]}")
            url = "https://bored.api.lewagon.com/api/activity"
            if params:
                url += "?" + "&".join(params)
            data, err = _proxy_json(url)
            if err:
                return self._send_json({"error": err}, 502)
            return self._send_json({"ok": True, "activity": data})
        return super().do_GET()

    def do_POST(self):
        p = urlparse(self.path)
        p = p._replace(path=self._norm_path(p.path))
        if p.path == "/api/auth":
            try:
                length = int(self.headers.get("Content-Length", 0))
                body = json.loads(self.rfile.read(length) or b"{}")
            except Exception:
                return self._send_json({"error": "bad json"}, 400)
            # установка/смена пароля: по Bearer-токену ИЛИ по initData (с экрана входа)
            if body.get("setPassword"):
                user = self._auth_user()
                if user is None:
                    init_data = (body.get("initData") or "").strip()
                    if init_data:
                        tg_user = miniapp_auth.verify_init_data(init_data, miniapp_auth.load_bot_token())
                        if tg_user and int(tg_user.get("id", 0)):
                            c = miniapp_auth._conn()
                            row = c.execute("SELECT * FROM users WHERE telegram_id=?", (int(tg_user["id"]),)).fetchone()
                            c.close()
                            if row is not None:
                                ok, err = miniapp_auth.set_password(int(tg_user["id"]), body.get("password") or "")
                                if not ok:
                                    return self._send_json({"error": err}, 400)
                                return self._send_json({"ok": True})
                    return self._send_json({"error": "unauthorized"}, 401)
                ok, err = miniapp_auth.set_password(user["telegram_id"], body.get("password") or "")
                if not ok:
                    return self._send_json({"error": err}, 400)
                return self._send_json({"ok": True})
            init_data = (body.get("initData") or "").strip()
            # лог ТОЛЬКО длины и времени — сырые initData/токены не пишем (ни в файлы, ни в лог)
            sys.stderr.write("[auth] initData len=%d ts=%d\n" % (len(init_data), int(time.time())))
            if not init_data:
                # десктоп/браузер без Telegram: вход по логину + мастер-паролю
                username = (body.get("username") or "").strip()
                password = body.get("password") or ""
                if username and password:
                    payload, err = miniapp_auth.login_password(username, password)
                    if err:
                        sys.stderr.write("[auth] password login error: %s\n" % err)
                        return self._send_json({"error": err}, 403)
                    return self._send_json(payload)
                return self._send_json({"error": "initData required"}, 400)
            token = miniapp_auth.load_bot_token()
            payload, err = miniapp_auth.login(init_data, token)
            if err:
                sys.stderr.write("[auth] login error: %s\n" % err)
                return self._send_json({"error": err}, 403)
            return self._send_json(payload)
        if p.path == "/api/auth/logout":
            user = self._require_auth()
            if user is None:
                return
            h = self.headers.get("Authorization", "")
            miniapp_auth.logout(h[7:].strip())
            return self._send_json({"ok": True})
        if p.path == "/api/ai/chat":
            # AI-чат через OpenClaw gateway (не напрямую в DeepSeek).
            # BYOK-ключ пользователя, иначе общий AI (квота до вызова).
            user = self._require_auth()
            if user is None:
                return
            try:
                length = int(self.headers.get("Content-Length", 0))
                body = json.loads(self.rfile.read(length) or b"{}")
            except Exception:
                return self._send_json({"error": "bad json"}, 400)
            messages = body.get("messages") or []
            if not messages or not isinstance(messages, list):
                return self._send_json({"error": "messages required"}, 400)
            model = (body.get("model") or "deepseek/deepseek-v4-flash").strip()
            key_plain = None
            keys = miniapp_auth.list_api_keys(user["telegram_id"])
            if keys:
                key_plain = miniapp_auth.get_api_key(user["telegram_id"], keys[0]["id"])
            if not key_plain:
                ok, err = miniapp_auth.check_quota(user)
                if not ok:
                    return self._send_json({"error": err}, 429)
            try:
                req_body = json.dumps({"model": model, "messages": messages, "max_tokens": 2000}).encode()
                headers = {"Content-Type": "application/json"}
                headers["Authorization"] = "Bearer " + (key_plain or GATEWAY_TOKEN)
                req = urllib.request.Request(GATEWAY_URL + "/v1/chat/completions", data=req_body, headers=headers)
                with urllib.request.urlopen(req, timeout=120) as r:
                    d = json.loads(r.read().decode("utf-8", "replace"))
                return self._send_json(d)
            except Exception as ex:
                return self._send_json({"error": str(ex)}, 502)
        if p.path == "/api/keys":
            # BYOK: сохранить ключ (AES-256-GCM; в UI только хвост)
            user = self._require_auth()
            if user is None:
                return
            try:
                length = int(self.headers.get("Content-Length", 0))
                body = json.loads(self.rfile.read(length) or b"{}")
            except Exception:
                return self._send_json({"error": "bad json"}, 400)
            name = (body.get("name") or "").strip() or "Ключ"
            key = (body.get("key") or "").strip()
            if not key:
                return self._send_json({"error": "key required"}, 400)
            kid = miniapp_auth.add_api_key(user["telegram_id"], name, key)
            return self._send_json({"ok": True, "keys": miniapp_auth.list_api_keys(user["telegram_id"])})
        if p.path == "/api/admin/users":
            user = self._require_admin()
            if user is None:
                return
            try:
                length = int(self.headers.get("Content-Length", 0))
                body = json.loads(self.rfile.read(length) or b"{}")
            except Exception:
                return self._send_json({"error": "bad json"}, 400)
            tid = int(body.get("telegram_id") or 0)
            ok = miniapp_auth.set_user(
                tid,
                allowed=body.get("allowed"),
                role=body.get("role"),
                allow_global_ai=body.get("allow_global_ai"),
                quota_daily=body.get("quota_daily"),
            )
            if not ok:
                return self._send_json({"error": "cannot update (owner/last admin/not found)"}, 400)
            return self._send_json({"ok": True, "users": miniapp_auth.list_users()})
        if p.path == "/api/sources":
            if self._require_auth() is None:
                return
            try:
                length = int(self.headers.get("Content-Length", 0))
                body = json.loads(self.rfile.read(length) or b"{}")
            except Exception:
                return self._send_json({"error": "bad json"}, 400)
            name = (body.get("name") or "").strip()
            if not name:
                return self._send_json({"error": "name required"}, 400)
            stype = "RSS" if body.get("type") == "RSS" else "TG"
            if stype == "RSS":
                ok, err = _validate_source_url(name)
                if not ok:
                    return self._send_json({"error": err}, 400)
            sources = load_sources()
            if len(sources) >= MAX_SOURCES:
                return self._send_json({"error": f"лимит источников: {MAX_SOURCES}"}, 400)
            new_id = max([s["id"] for s in sources], default=0) + 1
            sources.append({
                "id": new_id,
                "type": stype,
                "name": name,
                "title": (body.get("title") or name).strip(),
            })
            save_sources(sources)
            DIGEST_CACHE["ts"] = 0  # сброс кеша дайджеста
            return self._send_json({"ok": True, "sources": sources})
        if p.path == "/api/translate":
            # Переводчик: прокси к MyMemory (бесплатно, без ключа, лимит 50K/день с email)
            if self._require_auth() is None:
                return
            try:
                length = int(self.headers.get("Content-Length", 0))
                body = json.loads(self.rfile.read(length) or b"{}")
            except Exception:
                return self._send_json({"error": "bad json"}, 400)
            text = (body.get("text") or "").strip()
            lang_from = (body.get("from") or "en").strip()
            lang_to = (body.get("to") or "ru").strip()
            if not text:
                return self._send_json({"error": "text required"}, 400)
            if len(text) > MYMEMORY_MAX_CHARS:
                return self._send_json({"error": f"text too long (max {MYMEMORY_MAX_CHARS})"}, 400)
            try:
                res = translate_mymemory(text, lang_from, lang_to)
            except MyMemoryError as ex:
                return self._send_json({"error": str(ex)}, 502)
            return self._send_json(res)
        return self._send_json({"error": "not found"}, 404)

    def do_DELETE(self):
        p = urlparse(self.path)
        p = p._replace(path=self._norm_path(p.path))
        if p.path == "/api/admin/users":
            user = self._require_admin()
            if user is None:
                return
            q = parse_qs(p.query)
            try:
                tid = int(q.get("telegram_id", ["0"])[0])
            except Exception:
                return self._send_json({"error": "bad id"}, 400)
            if not miniapp_auth.delete_user(tid):
                return self._send_json({"error": "cannot delete (owner or not found)"}, 400)
            return self._send_json({"ok": True, "users": miniapp_auth.list_users()})
        if p.path == "/api/keys":
            # BYOK: удалить ключ
            user = self._require_auth()
            if user is None:
                return
            q = parse_qs(p.query)
            try:
                kid = int(q.get("id", ["0"])[0])
            except Exception:
                return self._send_json({"error": "bad id"}, 400)
            miniapp_auth.delete_api_key(user["telegram_id"], kid)
            return self._send_json({"ok": True, "keys": miniapp_auth.list_api_keys(user["telegram_id"])})
        if p.path == "/api/sources":
            if self._require_auth() is None:
                return
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
    miniapp_auth.init_db()
    # миграция старых сессий: plaintext-токены → SHA-256 хеш (один раз, с сохранением данных)
    try:
        c = miniapp_auth._conn()
        cols = [r[1] for r in c.execute("PRAGMA table_info(sessions)").fetchall()]
        if "token" in cols and "token_hash" not in cols:
            c.execute("ALTER TABLE sessions RENAME TO sessions_legacy")
            c.execute("CREATE TABLE sessions (token_hash TEXT PRIMARY KEY, telegram_id INTEGER, created_at INTEGER, expires_at INTEGER)")
            rows = c.execute("SELECT token, telegram_id, created_at, expires_at FROM sessions_legacy").fetchall()
            for r in rows:
                c.execute(
                    "INSERT OR IGNORE INTO sessions (token_hash, telegram_id, created_at, expires_at) VALUES (?,?,?,?)",
                    (hashlib.sha256(r["token"].encode()).hexdigest(), r["telegram_id"], r["created_at"], r["expires_at"]),
                )
            c.execute("DROP TABLE sessions_legacy")
            c.commit()
        c.close()
    except Exception as ex:
        sys.stderr.write("[miniapp] session migration skipped: %s\n" % ex)
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
    start_cache_worker()  # фоновый тёплый кеш — запросы не ждут сеть/AI
    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    print(f"MiniApp server on :{port} (static: {STATIC})", flush=True)
    server.serve_forever()
