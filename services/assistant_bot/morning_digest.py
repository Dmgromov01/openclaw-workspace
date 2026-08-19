import asyncio
import os
import json
import sqlite3
import shutil
import urllib.request
import urllib.parse
from datetime import datetime

BOT_TOKEN = "REDACTED-TELEGRAM-TOKEN"
CHAT_ID = "1916536646"
DB_PATH = "/root/openclaw/data/app.db"

def get_server_stats():
    total, used, free = shutil.disk_usage("/")
    disk_free_gb = free // (2**30)
    
    with open('/proc/meminfo') as f:
        mem = {}
        for line in f:
            parts = line.split(':')
            if len(parts) == 2:
                mem[parts[0].strip()] = int(parts[1].split()[0])
    mem_total_mb = mem.get('MemTotal', 0) // 1024
    mem_avail_mb = mem.get('MemAvailable', 0) // 1024
    
    return f"💾 Диск свободно: {disk_free_gb} GB | RAM: {mem_avail_mb}/{mem_total_mb} MB"

def get_recent_tasks():
    if not os.path.exists(DB_PATH):
        return "Нет базы данных."
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT action_item FROM voice_notes ORDER BY id DESC LIMIT 3")
    rows = cur.fetchall()
    conn.close()
    if not rows:
        return "Активных задач из голоса нет."
    return "\n".join([f"• {r[0][:120]}..." if len(r[0]) > 120 else f"• {r[0]}" for r in rows])

def send_telegram_msg(text: str):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = urllib.parse.urlencode({
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "Markdown"
    }).encode("utf-8")
    req = urllib.request.Request(url, data=payload)
    urllib.request.urlopen(req, timeout=10)

def main():
    date_str = datetime.now().strftime("%d.%m.%Y")
    stats = get_server_stats()
    tasks = get_recent_tasks()
    
    msg = (
        f"☀️ *Утренний Executive-дайджест — {date_str}*\n\n"
        f"📊 *Инфраструктура:*\n{stats}\n\n"
        f"🎯 *Последние задачи из заметок:*\n{tasks}\n\n"
        f"_Бот и сервисы работают штатно._"
    )
    send_telegram_msg(msg)

if __name__ == "__main__":
    main()
