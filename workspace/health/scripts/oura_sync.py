#!/usr/bin/env python3
"""Sync Oura Ring data into local SQLite. Read-only against Oura API.

Handles OAuth2 access-token refresh automatically using the refresh_token
stored in .env by oura_oauth_exchange.py. Never prints secrets.
"""
import argparse
import json
import sqlite3
import sys
import time
from datetime import timedelta
from pathlib import Path

import requests

import oura_auth
from analytics import local_today

# Compatibility: the project documents the self-check as `oura_sync.py --oauth-check`.
if __name__ == "__main__" and "--oauth-check" in sys.argv:
    import oura_oauth_exchange as _oura_exchange
    sys.exit(_oura_exchange.cmd_oauth_check(None))

WORKSPACE = Path(__file__).resolve().parents[1]
DB_PATH = WORKSPACE / "data" / "oura.db"
API_BASE = "https://api.ouraring.com/v2/usercollection"

SCHEMA = """
CREATE TABLE IF NOT EXISTS daily_sleep (
    id TEXT PRIMARY KEY,
    day TEXT,
    score INTEGER,
    total_sleep_seconds INTEGER,
    deep_sleep_seconds INTEGER,
    rem_sleep_seconds INTEGER,
    efficiency REAL,
    latency_seconds INTEGER,
    resting_heart_rate REAL,
    hrv_average REAL,
    respiratory_rate REAL,
    raw_json TEXT,
    updated_at TEXT
);
CREATE TABLE IF NOT EXISTS daily_readiness (
    id TEXT PRIMARY KEY,
    day TEXT,
    score INTEGER,
    hrv_balance REAL,
    resting_heart_rate REAL,
    temperature_deviation REAL,
    raw_json TEXT,
    updated_at TEXT
);
CREATE TABLE IF NOT EXISTS daily_activity (
    id TEXT PRIMARY KEY,
    day TEXT,
    score INTEGER,
    steps INTEGER,
    calories INTEGER,
    active_calories INTEGER,
    sedentary_time INTEGER,
    raw_json TEXT,
    updated_at TEXT
);
CREATE TABLE IF NOT EXISTS workouts (
    id TEXT PRIMARY KEY,
    day TEXT,
    activity TEXT,
    duration_seconds INTEGER,
    calories INTEGER,
    intensity TEXT,
    raw_json TEXT
);
CREATE TABLE IF NOT EXISTS tags (
    id TEXT PRIMARY KEY,
    day TEXT,
    tag TEXT,
    comment TEXT,
    raw_json TEXT
);
"""


def refresh_access_token(env: dict[str, str]) -> dict[str, str]:
    client_id = env.get("OURA_CLIENT_ID", "")
    client_secret = env.get("OURA_CLIENT_SECRET", "")
    refresh_token = env.get("OURA_REFRESH_TOKEN", "")
    if not (client_id and client_secret and refresh_token):
        print(json.dumps({"error": "missing OAuth credentials for refresh"}), file=sys.stderr)
        sys.exit(1)
    # Delegated to oura_auth: exact documented parameters, form-encoded body,
    # HTTP Basic only as a fallback, single-use refresh-token rotation.
    try:
        payload = oura_auth.refresh_tokens(refresh_token, client_id, client_secret)
    except oura_auth.OuraOAuthError as exc:
        print(json.dumps({"error": exc.code, "status": exc.status, "diagnosis": exc.diagnosis},
                         ensure_ascii=False), file=sys.stderr)
        sys.exit(1)
    env["OURA_ACCESS_TOKEN"] = payload["access_token"]
    env["OURA_REFRESH_TOKEN"] = payload.get("refresh_token", refresh_token)
    env["OURA_TOKEN_EXPIRES_AT"] = str(int(time.time()) + int(payload.get("expires_in", 86400)))
    oura_auth.write_env(env)
    return env


def get_access_token() -> str:
    env = oura_auth.read_env()
    expires_at = int(env.get("OURA_TOKEN_EXPIRES_AT", "0") or "0")
    if not env.get("OURA_ACCESS_TOKEN") or time.time() >= expires_at - 60:
        env = refresh_access_token(env)
    return env["OURA_ACCESS_TOKEN"]


def get_db() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB_PATH)
    con.executescript(SCHEMA)
    return con


# --- Full coverage: every Oura v2 collection, stored as raw payloads ---------
# Paths are case/underscore exact: heartrate has no underscore, vO2_max has a
# capital O. "kind" selects the request parameters the collection expects.
ENDPOINT_SPECS = (
    ("personal_info", "none"),
    ("daily_activity", "date"),
    ("daily_cardiovascular_age", "date"),
    ("daily_readiness", "date"),
    ("daily_resilience", "date"),
    ("daily_sleep", "date"),
    ("daily_spo2", "date"),
    ("daily_stress", "date"),
    ("enhanced_tag", "date"),
    ("heartrate", "datetime"),
    ("rest_mode_period", "date"),
    ("ring_configuration", "none"),
    ("session", "date"),
    ("sleep", "date"),
    ("sleep_time", "date"),
    ("tag", "date"),
    ("vO2_max", "date"),
    ("workout", "date"),
)


def ensure_raw_table(con: sqlite3.Connection) -> None:
    con.executescript(
        """
CREATE TABLE IF NOT EXISTS oura_raw (
    endpoint TEXT NOT NULL,
    item_key TEXT NOT NULL,
    day TEXT,
    payload TEXT,
    fetched_at TEXT,
    PRIMARY KEY (endpoint, item_key)
);
"""
    )


def fetch_any(endpoint: str, token: str, kind: str, start: str, end: str) -> list:
    """Fetch any v2 collection, choosing params by kind, following next_token."""
    headers = {"Authorization": "Bearer " + token}
    if kind == "datetime":
        # Oura rejects datetime collections spanning more than 30 days
        # (heartrate: "the time between start and endtime has to be less than or
        # equal to 30 days"), so walk the range in <=30-day windows.
        from datetime import date
        first, last = date.fromisoformat(start), date.fromisoformat(end)
        items: list = []
        cur = first
        while cur < last:
            window_end = min(cur + timedelta(days=30), last)
            items.extend(_fetch_window(endpoint, headers, {
                "start_datetime": cur.isoformat() + "T00:00:00+00:00",
                "end_datetime": window_end.isoformat() + "T00:00:00+00:00",
            }))
            cur = window_end
        return items
    if kind == "date":
        params = {"start_date": start, "end_date": end}
    else:
        params = {}
    return _fetch_window(endpoint, headers, params)


def _fetch_window(endpoint: str, headers: dict, params: dict) -> list:
    """Fetch one request window, following next_token to the end."""
    items: list = []
    while True:
        resp = requests.get(API_BASE + "/" + endpoint, headers=headers, params=params, timeout=30)
        if resp.status_code >= 400:
            raise oura_auth.OuraOAuthError(resp.status_code, "api_error", resp.text[:200],
                                           oura_auth.diagnose_api(resp.status_code, endpoint))
        body = resp.json()
        if isinstance(body, dict) and isinstance(body.get("data"), list):
            items.extend(body["data"])
            nxt = body.get("next_token")
        else:
            items.append(body)
            nxt = None
        if not nxt:
            return items
        params["next_token"] = nxt


def upsert_raw(con: sqlite3.Connection, endpoint: str, items: list) -> int:
    now = local_today().isoformat()
    rows = []
    for i, item in enumerate(items):
        if isinstance(item, dict):
            key = str(item.get("id") or item.get("day") or item.get("timestamp") or i)
            day = item.get("day") or (str(item.get("timestamp", ""))[:10] or None)
        else:
            key, day = str(i), None
        rows.append((endpoint, key, day, json.dumps(item, ensure_ascii=False), now))
    con.executemany(
        "INSERT OR REPLACE INTO oura_raw (endpoint, item_key, day, payload, fetched_at) "
        "VALUES (?, ?, ?, ?, ?)",
        rows,
    )
    return len(rows)


def sync_all(days: int) -> dict:
    """Pull EVERY v2 collection into oura_raw. Returns per-endpoint counts."""
    get_access_token()
    con = get_db()
    ensure_raw_table(con)
    start_s = (local_today() - timedelta(days=days)).isoformat()
    end_s = local_today().isoformat()
    counts: dict = {}
    errors: dict = {}
    try:
        for endpoint, kind in ENDPOINT_SPECS:
            try:
                items = fetch_any(endpoint, get_access_token(), kind, start_s, end_s)
                counts[endpoint] = upsert_raw(con, endpoint, items)
            except oura_auth.OuraOAuthError as exc:
                errors[endpoint] = str(exc.status) + " " + str(exc.code)
            except Exception as exc:
                errors[endpoint] = str(exc)[:120]
        con.commit()
    finally:
        con.close()
    return {"ok": not errors, "range": [start_s, end_s], "counts": counts,
            "errors": errors, "total": sum(counts.values())}


def raw_stats() -> dict:
    """Row counts already stored in oura_raw. No API calls, safe to poll."""
    con = get_db()
    ensure_raw_table(con)
    try:
        rows = con.execute(
            "SELECT endpoint, COUNT(*) FROM oura_raw GROUP BY endpoint ORDER BY endpoint"
        ).fetchall()
    finally:
        con.close()
    per = {str(name): int(n) for name, n in rows}
    try:
        size = DB_PATH.stat().st_size
    except OSError:
        size = None
    return {"db": str(DB_PATH), "db_bytes": size, "per_endpoint": per,
            "total": sum(per.values())}


def main() -> None:
    parser = argparse.ArgumentParser(description="Sync Oura data into SQLite")
    parser.add_argument("--days", type=int, default=7, help="How many days back to sync")
    args = parser.parse_args()

    result = sync_all(args.days)
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
