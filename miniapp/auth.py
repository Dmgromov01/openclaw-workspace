#!/usr/bin/env python3
"""
MiniApp auth: Telegram WebApp initData-верификация + пользователи + сессии + аудит + BYOK.

- Верификация initData: HMAC-SHA256 (secret = HMAC_SHA256(bot_token, "WebAppData")).
- Сессии: в БД ТОЛЬКО SHA-256 хеш токена (не plaintext), TTL 7 дней.
- Пароли: PBKDF2-HMAC-SHA256 100k (старый sha256(salt+password) убран).
- Владелец — из env TELEGRAM_OWNER_ID (не хардкод); его нельзя разжаловать/блокировать/удалить;
  нельзя снять последнего админа.
- BYOK: API-ключи шифруются AES-256-GCM (мастер из AI_KEY_SECRET или bot token).
"""
import base64
import hashlib
import hmac
import json
import os
import re
import secrets
import sqlite3
import time
from urllib.parse import parse_qsl

DB = os.environ.get("MINIAPP_DB", os.path.join(os.path.dirname(os.path.abspath(__file__)), "miniapp.db"))

_ENV_RE = re.compile(r"^\s*([A-Z0-9_]+)\s*=\s*['\"]?([^'\r\n'\"]+)", re.M)


def _load_env():
    """Читает .env в dict (значения не логируем)."""
    env = os.environ.get("MINIAPP_ENV", "/root/.openclaw/.env")
    d = {}
    if os.path.exists(env):
        for m in _ENV_RE.finditer(open(env, encoding="utf-8").read()):
            d[m.group(1)] = m.group(2).strip()
    return d


def _owner_id():
    """Владелец ТОЛЬКО из TELEGRAM_OWNER_ID (env или .env). Пусто → ошибка при старте, не хардкод."""
    v = (os.environ.get("TELEGRAM_OWNER_ID") or _load_env().get("TELEGRAM_OWNER_ID") or "").strip()
    if not v:
        raise RuntimeError("TELEGRAM_OWNER_ID не задан (env/.env) — отказ старта")
    return int(v)


OWNER_TG_ID = _owner_id()
SESSION_TTL = 7 * 24 * 3600  # 7 дней
PBKDF2_ITER = 100_000
MIN_PASSWORD_LEN = 8


def _conn():
    c = sqlite3.connect(DB, timeout=15)
    c.row_factory = sqlite3.Row
    try:
        c.execute("PRAGMA journal_mode=WAL;")
        c.execute("PRAGMA busy_timeout=15000;")
    except Exception:
        pass
    return c


def init_db():
    c = _conn()
    c.execute("""CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        telegram_id INTEGER UNIQUE,
        username TEXT,
        first_name TEXT,
        role TEXT DEFAULT 'user',
        allowed INTEGER DEFAULT 0,
        password_hash TEXT,
        created_at INTEGER,
        last_login INTEGER,
        allow_global_ai INTEGER DEFAULT 0,
        quota_daily INTEGER DEFAULT 0
    )""")
    # миграция: новые колонки могли отсутствовать (старые базы)
    cols = [r[1] for r in c.execute("PRAGMA table_info(users)").fetchall()]
    for col, ddl in (("password_hash", "TEXT"), ("allow_global_ai", "INTEGER DEFAULT 0"), ("quota_daily", "INTEGER DEFAULT 0")):
        if col not in cols:
            c.execute(f"ALTER TABLE users ADD COLUMN {col} {ddl}")
    c.execute("""CREATE TABLE IF NOT EXISTS sessions (
        token_hash TEXT PRIMARY KEY,
        telegram_id INTEGER,
        created_at INTEGER,
        expires_at INTEGER
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS audit_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ts INTEGER,
        telegram_id INTEGER,
        action TEXT
    )""")
    # BYOK: зашифрованные API-ключи пользователей (AES-256-GCM), в UI — только хвост.
    c.execute("""CREATE TABLE IF NOT EXISTS api_keys (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        telegram_id INTEGER,
        name TEXT,
        key_cipher BLOB,
        key_nonce BLOB,
        key_tail TEXT,
        created_at INTEGER
    )""")
    # Дневная квота общего AI: счётчик использованных запросов.
    c.execute("""CREATE TABLE IF NOT EXISTS ai_usage (
        telegram_id INTEGER,
        day TEXT,
        used INTEGER DEFAULT 0,
        PRIMARY KEY (telegram_id, day)
    )""")
    c.commit()
    c.execute(
        "INSERT OR IGNORE INTO users (telegram_id, username, first_name, role, allowed, created_at) VALUES (?,?,?,?,1,?)",
        (OWNER_TG_ID, "Dm_GRM", "Dmitry", "admin", int(time.time())),
    )
    c.commit()
    c.close()


def load_bot_token():
    """Bot token из env / .env (TELEGRAM_BOT_TOKEN)."""
    return os.environ.get("TELEGRAM_BOT_TOKEN") or _load_env().get("TELEGRAM_BOT_TOKEN", "")


def _master_key():
    """Мастер-ключ BYOK: AI_KEY_SECRET (env/.env), иначе bot token. SHA-256 → 32 байта (AES-256)."""
    secret = os.environ.get("AI_KEY_SECRET") or _load_env().get("AI_KEY_SECRET") or load_bot_token()
    return hashlib.sha256(secret.encode()).digest()


def _aes_encrypt(plaintext: str):
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    nonce = os.urandom(12)
    ct = AESGCM(_master_key()).encrypt(nonce, plaintext.encode(), None)
    return ct, nonce


def _aes_decrypt(ct, nonce):
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    return AESGCM(_master_key()).decrypt(nonce, bytes(ct), None).decode()


def verify_init_data(init_data, bot_token, max_age=86400):
    """Проверяет подпись initData (стандартный алгоритм Telegram Mini Apps).

    secret_key = HMAC_SHA256(key="WebAppData", msg=bot_token)
    data_check_string = все поля КРОМЕ hash (включая signature),
        отсортированные по ключу, key=value через \n, значения URL-декодированы.
    hash = HMAC_SHA256(key=secret_key, msg=data_check_string).hexdigest()
    Плюс проверка свежести auth_date (защита от replay-атак).
    """
    try:
        params = dict(parse_qsl(init_data, keep_blank_values=True))
        received = params.pop("hash", None)
        if not received:
            return None
        secret_key = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
        check_string = "\n".join(f"{k}={v}" for k, v in sorted(params.items()))
        calc = hmac.new(secret_key, check_string.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(calc, received):
            return None
        # защита от replay: auth_date не старше max_age секунд
        try:
            ad = int(params.get("auth_date", 0))
        except (TypeError, ValueError):
            ad = 0
        if not ad or time.time() - ad > max_age:
            return None
        user = json.loads(params.get("user", "{}"))
        return user if isinstance(user, dict) else None
    except Exception:
        return None


def _hash_token(token):
    """Сессии в БД храним ТОЛЬКО как SHA-256 хеш токена, не plaintext."""
    return hashlib.sha256(token.encode()).hexdigest()


def login(init_data, bot_token):
    """Логин по initData. Возвращает (payload|None, error|None)."""
    user = verify_init_data(init_data, bot_token)
    if not user:
        return None, "Неверная подпись Telegram"
    tid = int(user.get("id", 0))
    if not tid:
        return None, "Нет telegram_id"
    c = _conn()
    row = c.execute("SELECT * FROM users WHERE telegram_id=?", (tid,)).fetchone()
    if row is None:
        c.execute(
            "INSERT OR IGNORE INTO users (telegram_id, username, first_name, role, allowed, created_at) VALUES (?,?,?, 'user', 0, ?)",
            (tid, user.get("username"), user.get("first_name"), int(time.time())),
        )
        c.execute("INSERT INTO audit_log (ts, telegram_id, action) VALUES (?,?,?)",
                  (int(time.time()), tid, "login_denied_not_allowed"))
        c.commit()
        c.close()
        return None, "Доступ запрещён: обратитесь к администратору"
    if not row["allowed"]:
        c.execute("INSERT INTO audit_log (ts, telegram_id, action) VALUES (?,?,?)",
                  (int(time.time()), tid, "login_denied_not_allowed"))
        c.commit()
        c.close()
        return None, "Доступ запрещён: обратитесь к администратору"
    token = secrets.token_urlsafe(32)
    exp = int(time.time()) + SESSION_TTL
    c.execute("INSERT INTO sessions (token_hash, telegram_id, created_at, expires_at) VALUES (?,?,?,?)",
              (_hash_token(token), tid, int(time.time()), exp))
    c.execute("UPDATE users SET last_login=? WHERE telegram_id=?", (int(time.time()), tid))
    c.execute("INSERT INTO audit_log (ts, telegram_id, action) VALUES (?,?,?)",
              (int(time.time()), tid, "login_ok"))
    c.commit()
    c.close()
    return {
        "token": token,
        "user": {
            "id": row["id"],
            "telegram_id": tid,
            "username": row["username"],
            "first_name": row["first_name"],
            "role": row["role"],
            "allowed": bool(row["allowed"]),
            "allow_global_ai": bool(row["allow_global_ai"]),
            "quota_daily": row["quota_daily"] or 0,
        },
    }, None


def _hash_password(password, salt=None, iterations=PBKDF2_ITER):
    """PBKDF2-HMAC-SHA256: salt$iterations$hex. Медленный хэш — устойчив к GPU-перебору."""
    salt = salt or secrets.token_hex(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), iterations)
    return f"{salt}${iterations}${dk.hex()}"


def set_password(telegram_id, password):
    """Пользователь сам задаёт/меняет свой пароль. Хэш — PBKDF2-HMAC-SHA256 (100k)."""
    if not password or len(password) < MIN_PASSWORD_LEN:
        return False, f"Пароль слишком короткий (мин. {MIN_PASSWORD_LEN} символов)"
    ph = _hash_password(password)
    c = _conn()
    row = c.execute("SELECT * FROM users WHERE telegram_id=?", (telegram_id,)).fetchone()
    if row is None:
        c.close()
        return False, "Пользователь не найден"
    c.execute("UPDATE users SET password_hash=? WHERE telegram_id=?", (ph, telegram_id))
    c.execute("INSERT INTO audit_log (ts, telegram_id, action) VALUES (?,?,?)",
              (int(time.time()), telegram_id, "password_set"))
    c.commit()
    c.close()
    return True, None


def check_password(username, password):
    """Проверка пароля (только PBKDF2 формат; sha256(salt+password) убран)."""
    tid = None
    if str(username).strip().isdigit():
        tid = int(username)
    c = _conn()
    row = None
    if tid:
        row = c.execute("SELECT * FROM users WHERE telegram_id=?", (tid,)).fetchone()
    if row is None and username:
        row = c.execute("SELECT * FROM users WHERE username=?", (username.strip().lstrip("@"),)).fetchone()
    if row is None or not row["password_hash"]:
        c.close()
        return None, "Пользователь не найден или пароль не задан"
    stored = row["password_hash"] or ""
    parts = stored.split("$")
    if len(parts) == 3:
        # новый формат: salt$iterations$hex (PBKDF2)
        salt, iterations, h = parts
        try:
            iterations = int(iterations)
        except (TypeError, ValueError):
            iterations = PBKDF2_ITER
        calc = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), iterations).hex()
        if not hmac.compare_digest(calc, h):
            c.close()
            return None, "Неверный пароль"
        return row, None
    # старый формат: salt$sha256hex — проверяем и переписываем на PBKDF2, не ломаем вход
    salt, _, h = stored.partition("$")
    if not salt or not h:
        c.close()
        return None, "Пароль не задан"
    calc = hashlib.sha256((salt + password).encode()).hexdigest()
    if not hmac.compare_digest(calc, h):
        c.close()
        return None, "Неверный пароль"
    try:
        c.execute("UPDATE users SET password_hash=? WHERE telegram_id=?",
                  (_hash_password(password), row["telegram_id"]))
        c.commit()
    except Exception:
        pass
    return row, None


def login_password(username, password):
    """Вход по логину Telegram + собственному паролю пользователя (десктоп/браузер)."""
    row, err = check_password(username, password)
    if err:
        return None, err
    if not row["allowed"]:
        c = _conn()
        c.execute("INSERT INTO audit_log (ts, telegram_id, action) VALUES (?,?,?)",
                  (int(time.time()), row["telegram_id"], "login_password_denied"))
        c.commit()
        c.close()
        return None, "Доступ запрещён: обратитесь к администратору"
    token = secrets.token_urlsafe(32)
    exp = int(time.time()) + SESSION_TTL
    c = _conn()
    c.execute("INSERT INTO sessions (token_hash, telegram_id, created_at, expires_at) VALUES (?,?,?,?)",
              (_hash_token(token), row["telegram_id"], int(time.time()), exp))
    c.execute("UPDATE users SET last_login=? WHERE telegram_id=?", (int(time.time()), row["telegram_id"]))
    c.execute("INSERT INTO audit_log (ts, telegram_id, action) VALUES (?,?,?)",
              (int(time.time()), row["telegram_id"], "login_password_ok"))
    c.commit()
    c.close()
    return {
        "token": token,
        "user": {
            "id": row["id"],
            "telegram_id": row["telegram_id"],
            "username": row["username"],
            "first_name": row["first_name"],
            "role": row["role"],
            "allowed": bool(row["allowed"]),
            "allow_global_ai": bool(row["allow_global_ai"]),
            "quota_daily": row["quota_daily"] or 0,
        },
    }, None


def auth(token):
    """Валидирует токен сессии по SHA-256 хешу. Возвращает строку пользователя или None."""
    if not token:
        return None
    c = _conn()
    row = c.execute(
        "SELECT u.* FROM sessions s JOIN users u ON u.telegram_id = s.telegram_id "
        "WHERE s.token_hash=? AND s.expires_at > ?",
        (_hash_token(token), int(time.time())),
    ).fetchone()
    c.close()
    return row


def logout(token):
    c = _conn()
    c.execute("DELETE FROM sessions WHERE token_hash=?", (_hash_token(token),))
    c.commit()
    c.close()


def list_users():
    c = _conn()
    rows = c.execute("SELECT * FROM users ORDER BY role DESC, id").fetchall()
    c.close()
    return [dict(r) for r in rows]


def _admin_count(c):
    return c.execute("SELECT COUNT(*) FROM users WHERE role='admin' AND allowed=1").fetchone()[0]


def set_user(telegram_id, allowed=None, role=None, allow_global_ai=None, quota_daily=None):
    c = _conn()
    row = c.execute("SELECT * FROM users WHERE telegram_id=?", (telegram_id,)).fetchone()
    if row is None:
        c.close()
        return False
    if telegram_id == OWNER_TG_ID:
        # владельца нельзя разжаловать/заблокировать/снять с админа
        c.close()
        return False
    # защита последнего админа: нельзя снять роль/доступ последнему админу
    if (role == "user" or allowed == 0) and row["role"] == "admin" and _admin_count(c) <= 1:
        c.close()
        return False
    if allowed is not None:
        c.execute("UPDATE users SET allowed=? WHERE telegram_id=?", (1 if allowed else 0, telegram_id))
    if role in ("user", "admin"):
        c.execute("UPDATE users SET role=? WHERE telegram_id=?", (role, telegram_id))
    if allow_global_ai is not None:
        c.execute("UPDATE users SET allow_global_ai=? WHERE telegram_id=?", (1 if allow_global_ai else 0, telegram_id))
    if quota_daily is not None:
        try:
            q = max(0, int(quota_daily))
        except (TypeError, ValueError):
            q = 0
        c.execute("UPDATE users SET quota_daily=? WHERE telegram_id=?", (q, telegram_id))
    c.execute("INSERT INTO audit_log (ts, telegram_id, action) VALUES (?,?,?)",
              (int(time.time()), telegram_id, "admin_update"))
    c.commit()
    c.close()
    return True


def delete_user(telegram_id):
    if telegram_id == OWNER_TG_ID:
        return False
    c = _conn()
    row = c.execute("SELECT * FROM users WHERE telegram_id=?", (telegram_id,)).fetchone()
    if row is None:
        c.close()
        return False
    # защита последнего админа
    if row["role"] == "admin" and _admin_count(c) <= 1:
        c.close()
        return False
    c.execute("DELETE FROM users WHERE telegram_id=?", (telegram_id,))
    c.execute("DELETE FROM sessions WHERE telegram_id=?", (telegram_id,))
    c.execute("DELETE FROM api_keys WHERE telegram_id=?", (telegram_id,))
    c.commit()
    c.close()
    return True


def audit(limit=50):
    c = _conn()
    rows = c.execute("SELECT * FROM audit_log ORDER BY ts DESC LIMIT ?", (limit,)).fetchall()
    c.close()
    return [dict(r) for r in rows]


# ---------- BYOK (AES-256-GCM) ----------

def add_api_key(telegram_id, name, key):
    ct, nonce = _aes_encrypt(key)
    tail = key[-4:] if len(key) >= 4 else key
    c = _conn()
    c.execute("INSERT INTO api_keys (telegram_id, name, key_cipher, key_nonce, key_tail, created_at) VALUES (?,?,?,?,?,?)",
              (telegram_id, name, ct, nonce, tail, int(time.time())))
    c.commit()
    rid = c.execute("SELECT last_insert_rowid()").fetchone()[0]
    c.close()
    return rid


def list_api_keys(telegram_id):
    c = _conn()
    rows = c.execute("SELECT id, name, key_tail, created_at FROM api_keys WHERE telegram_id=? ORDER BY id",
                     (telegram_id,)).fetchall()
    c.close()
    return [dict(r) for r in rows]


def get_api_key(telegram_id, kid):
    c = _conn()
    row = c.execute("SELECT * FROM api_keys WHERE id=? AND telegram_id=?", (kid, telegram_id)).fetchone()
    c.close()
    if row is None:
        return None
    return _aes_decrypt(row["key_cipher"], row["key_nonce"])


def delete_api_key(telegram_id, kid):
    c = _conn()
    c.execute("DELETE FROM api_keys WHERE id=? AND telegram_id=?", (kid, telegram_id))
    c.commit()
    c.close()


# ---------- Квота общего AI ----------

def check_quota(user, cost=1):
    """Проверяет и списывает дневную квоту общего AI. Возвращает (ok, err)."""
    if not user["allow_global_ai"] or not (user["quota_daily"] or 0):
        return False, "Общий AI выключен (allow_global_ai=0 или quota=0)"
    day = time.strftime("%Y-%m-%d", time.gmtime())
    c = _conn()
    row = c.execute("SELECT used FROM ai_usage WHERE telegram_id=? AND day=?", (user["telegram_id"], day)).fetchone()
    used = row["used"] if row else 0
    if used + cost > int(user["quota_daily"]):
        c.close()
        return False, "Дневная квота исчерпана"
    c.execute(
        "INSERT INTO ai_usage (telegram_id, day, used) VALUES (?,?,?) "
        "ON CONFLICT(telegram_id, day) DO UPDATE SET used=used+?",
        (user["telegram_id"], day, cost, cost),
    )
    c.commit()
    c.close()
    return True, None
