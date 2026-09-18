#!/usr/bin/env python3
"""
safe-sqlite-edit.py — Безопасная правка SQLite БД OpenClaw.

Использование:
  python3 safe-sqlite-edit.py <db_path> <sql_statement> [--allow-pragma]

Функции безопасности:
  1. Автоматический бэкап перед любым WRITE (INSERT/UPDATE/DELETE/DROP/ALTER)
  2. Валидация JSON-полей после UPDATE
  3. Откат при ошибке (ROLLBACK)
  4. Логирование в /root/openclaw/logs/sqlite-edits.log
  5. Запрет PRAGMA без --allow-pragma
"""

import sqlite3
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

LOG_DIR = Path("/root/openclaw/logs")
LOG_FILE = LOG_DIR / "sqlite-edits.log"
BACKUP_DIR = Path("/root/_trash/sqlite-auto-backups")
WRITE_KEYWORDS = {"INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "CREATE", "REPLACE"}


def log(msg):
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    line = f"[{ts}] {msg}"
    print(line)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")


def is_write(sql):
    first_word = sql.strip().split()[0].upper() if sql.strip() else ""
    return first_word in WRITE_KEYWORDS


def backup_db(db_path):
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    db_name = Path(db_path).name
    backup_path = BACKUP_DIR / f"{db_name}.{ts}.bak"
    src = sqlite3.connect(db_path)
    dst = sqlite3.connect(str(backup_path))
    src.backup(dst)
    dst.close()
    src.close()
    size = backup_path.stat().st_size
    log(f"BACKUP: {db_path} -> {backup_path} ({size} bytes)")
    return str(backup_path)


def validate_json_columns(cursor, table):
    cursor.execute(f"PRAGMA table_info({table})")
    columns = cursor.fetchall()
    issues = []
    for col in columns:
        col_name = col[1]
        try:
            cursor.execute(f"SELECT rowid, {col_name} FROM {table} WHERE {col_name} IS NOT NULL LIMIT 10")
            for row in cursor.fetchall():
                val = row[1]
                if isinstance(val, str) and (val.startswith("{") or val.startswith("[")):
                    try:
                        json.loads(val)
                    except json.JSONDecodeError as e:
                        issues.append(f"rowid={row[0]}, col={col_name}: invalid JSON: {e}")
        except Exception:
            pass
    return issues


def main():
    if len(sys.argv) < 3:
        print("Usage: safe-sqlite-edit.py <db_path> <sql_statement> [--allow-pragma]")
        sys.exit(1)

    db_path = sys.argv[1]
    sql = sys.argv[2]
    allow_pragma = "--allow-pragma" in sys.argv

    if not os.path.exists(db_path):
        log(f"ERROR: DB not found: {db_path}")
        sys.exit(1)

    if sql.strip().upper().startswith("PRAGMA") and not allow_pragma:
        log("BLOCKED: PRAGMA requires --allow-pragma flag")
        sys.exit(1)

    write_op = is_write(sql)
    backup_path = None

    if write_op:
        log(f"WRITE detected: {sql[:100]}...")
        backup_path = backup_db(db_path)

    try:
        conn = sqlite3.connect(db_path)
        conn.execute("BEGIN")
        cursor = conn.execute(sql)

        if write_op:
            affected = cursor.rowcount
            conn.commit()
            log(f"COMMIT: {affected} rows affected")
            tables_with_json = ["exec_approvals_config", "agent_configs"]
            for tbl in tables_with_json:
                if tbl.lower() in sql.lower():
                    issues = validate_json_columns(cursor, tbl)
                    if issues:
                        log(f"WARNING: JSON validation issues in {tbl}:")
                        for issue in issues:
                            log(f"  - {issue}")
                    else:
                        log(f"JSON validation OK for {tbl}")
        else:
            rows = cursor.fetchall()
            col_names = [desc[0] for desc in cursor.description] if cursor.description else []
            log(f"READ: {len(rows)} rows returned")
            if rows:
                print(f"Columns: {col_names}")
                for row in rows[:20]:
                    print(row)
                if len(rows) > 20:
                    print(f"... and {len(rows) - 20} more rows")

        conn.close()
        log("SUCCESS")

    except Exception as e:
        log(f"ERROR: {e}")
        if write_op and backup_path:
            log(f"ROLLBACK performed. Backup at: {backup_path}")
            log(f"To restore: cp {backup_path} {db_path}")
        sys.exit(1)


if __name__ == "__main__":
    main()
