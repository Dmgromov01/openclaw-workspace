#!/usr/bin/env python3
"""
MiniApp auth: Telegram WebApp initData-верификация + пользователи + сессии + аудит.

- Верификация initData: HMAC-SHA256 (secret = HMAC_SHA256(bot_token, "WebAppData")).
- Пользователи: sqlite (users, sessions, audit_log).
- Владелец (1916536646) — всегда admin; остальные допускаются админом.
"""
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
OWNER_TG_ID = int(os.environ.get("MINIAPP_OWNER_TG_ID", "1916536646"))
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
        last_login INTEGER
    )""")
    # миграция: колонка password_hash могла отсутствовать (старые базы)
    cols = [r[1] for r in c.execute("PRAGMA table_info(users)").fetchall()]
    if "password_hash" not in cols:
        c.execute("ALTER TABLE users ADD COLUMN password_hash TEXT")
    c.execute("""CREATE TABLE IF NOT EXISTS sessions (
        token TEXT PRIMARY KEY,
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
    c.commit()
    c.execute(
        "INSERT OR IGNORE INTO users (telegram_id, username, first_name, role, allowed, created_at) VALUES (?,?,?,?,1,?)",
        (OWNER_TG_ID, "Dm_GRM", "Dmitry", "admin", int(time.time())),
    )
    c.commit()
    c.close()


_ENV_RE = re.compile(r"^\s*TELEGRAM_BOT_TOKEN\s*=\s*['\"]?([^'\"\s]+)", re.M)


def load_bot_token():
    """Bot token из /root/.openclaw/.env (TELEGRAM_BOT_TOKEN=...). Регэксп вместо ручного парсинга."""
    env = os.environ.get("MINIAPP_ENV", "/root/.openclaw/.env")
    if os.path.exists(env):
        m = _ENV_RE.search(open(env, encoding="utf-8").read())
        if m:
            return m.group(1)
    return ""


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
    c.execute("INSERT INTO sessions (token, telegram_id, created_at, expires_at) VALUES (?,?,?,?)",
              (token, tid, int(time.time()), exp))
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
        },
    }, None


def _hash_password(password, salt=None, iterations=PBKDF2_ITER):
    """PBKDF2-HMAC-SHA256: salt$iterations$hex. Медленный хэш — устойчив к GPU-перебору."""
    salt = salt or secrets.token_hex(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), iterations)
    return f"{salt}${iterations}${dk.hex()}"


def set_password(telegram_id, password):
    """Пользователь сам задаёт/меняет свой пароль. Хэш — PBKDF2-HMAC-SHA256."""
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
    """Проверка пароля пользователя. username = username Telegram или telegram_id."""
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
    if len(parts) == 3:  # новый формат: salt$iterations$hex
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
    # старый формат: salt$sha256hex — проверяем и пересохраняем на PBKDF2
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
    c.execute("INSERT INTO sessions (token, telegram_id, created_at, expires_at) VALUES (?,?,?,?)",
              (token, row["telegram_id"], int(time.time()), exp))
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
        },
    }, None


def auth(token):
    """Валидирует токен сессии. Возвращает строку пользователя (users join) или None."""
    if not token:
        return None
    c = _conn()
    row = c.execute(
        "SELECT u.* FROM sessions s JOIN users u ON u.telegram_id = s.telegram_id "
        "WHERE s.token=? AND s.expires_at > ?",
        (token, int(time.time())),
    ).fetchone()
    c.close()
    return row


def logout(token):
    c = _conn()
    c.execute("DELETE FROM sessions WHERE token=?", (token,))
    c.commit()
    c.close()


def list_users():
    c = _conn()
    rows = c.execute("SELECT * FROM users ORDER BY role DESC, id").fetchall()
    c.close()
    return [dict(r) for r in rows]


def set_user(telegram_id, allowed=None, role=None):
    c = _conn()
    row = c.execute("SELECT * FROM users WHERE telegram_id=?", (telegram_id,)).fetchone()
    if row is None:
        c.close()
        return False
    if telegram_id == OWNER_TG_ID:
        # владельца нельзя разжаловать/заблокировать
        c.close()
        return False
    if allowed is not None:
        c.execute("UPDATE users SET allowed=? WHERE telegram_id=?", (1 if allowed else 0, telegram_id))
    if role in ("user", "admin"):
        c.execute("UPDATE users SET role=? WHERE telegram_id=?", (role, telegram_id))
    c.execute("INSERT INTO audit_log (ts, telegram_id, action) VALUES (?,?,?)",
              (int(time.time()), telegram_id, "admin_update"))
    c.commit()
    c.close()
    return True


def delete_user(telegram_id):
    if telegram_id == OWNER_TG_ID:
        return False
    c = _conn()
    c.execute("DELETE FROM users WHERE telegram_id=?", (telegram_id,))
    c.execute("DELETE FROM sessions WHERE telegram_id=?", (telegram_id,))
    c.commit()
    c.close()
    return True


def audit(limit=50):
    c = _conn()
    rows = c.execute("SELECT * FROM audit_log ORDER BY ts DESC LIMIT ?", (limit,)).fetchall()
    c.close()
    return [dict(r) for r in rows]
