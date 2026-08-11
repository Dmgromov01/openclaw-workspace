#!/usr/bin/env python3
"""
meme_fetcher.py — присылает свежий мем из открытых TG-каналов владельцу в Telegram.

Механизм:
1. curl через VPN (SOCKS 127.0.0.1:10808, Германия) на t.me/s/<канал>
2. Парсит HTML → собирает прямые ссылки на картинки постов (cdn*.telesco.pe)
3. Скачивает первый найденный мем
4. Отправляет через Bot API владельцу (owner chat id)

Расписание мемов: cron 08:00 и 18:00 (MSK), максимум 2 в сутки.
"""
import os
import re
import sys
import json
import subprocess
import random

# --- конфиг ---
SOCKS_PROXY = "socks5h://127.0.0.1:10808"
CHANNELS = ["memach", "sarcasm"]  # приоритет: @memach (подтверждён пользователем), запасной: @sarcasm
OWNER_CHAT_ID = 1916536646
BOT_TOKEN_PATH = "/root/.openclaw/openclaw.json"
TMP_DIR = "/root/.openclaw/workspace/calendar/memes"
STAMP_FILE = os.path.join(TMP_DIR, "last.txt")

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"


def get_bot_token():
    with open(BOT_TOKEN_PATH) as f:
        cfg = json.load(f)
    return cfg["channels"]["telegram"]["botToken"]


def fetch_channel(channel):
    """Возвращает список прямых ссылок на картинки постов канала."""
    url = f"https://t.me/s/{channel}"
    try:
        html = subprocess.run(
            ["curl", "-s", "--socks5-hostname", SOCKS_PROXY,
             "-A", UA, "--max-time", "20", url],
            capture_output=True, text=True, timeout=25
        ).stdout
    except Exception as e:
        print(f"  fetch {channel}: {e}")
        return []
    # реальные посты-мемы лежат в photo_wrap (background-image), а НЕ в <img src> (там аватар канала)
    imgs = re.findall(
        r'class="tgme_widget_message_photo_wrap[^"]*"[^>]*background-image:\s*url\(.([^)]+)\)',
        html
    )
    # убираем дубликаты, сохраняя порядок (первые = свежие)
    seen = set()
    uniq = []
    for u in imgs:
        if u not in seen:
            seen.add(u)
            uniq.append(u)
    return uniq


def download(url, dest):
    r = subprocess.run(
        ["curl", "-s", "-L", "--socks5-hostname", SOCKS_PROXY,
         "-A", UA, "--max-time", "25", url, "-o", dest],
        capture_output=True, text=True, timeout=30)
    return r.returncode == 0 and os.path.exists(dest) and os.path.getsize(dest) > 500


def send_photo(token, chat_id, photo_path, caption=""):
    """Отправляет фото через Bot API (multipart)."""
    import requests
    url = f"https://api.telegram.org/bot{token}/sendPhoto"
    with open(photo_path, "rb") as f:
        files = {"photo": (os.path.basename(photo_path), f, "image/jpeg")}
        data = {"chat_id": chat_id, "caption": caption}
        resp = requests.post(url, files=files, data=data, timeout=30)
    return resp.status_code == 200, resp.json()


def load_used():
    if os.path.exists(STAMP_FILE):
        with open(STAMP_FILE) as f:
            return set(x.strip() for x in f.read().splitlines() if x.strip())
    return set()


def save_used(used, url):
    # keep last 200 used to avoid repeats
    used.add(url)
    with open(STAMP_FILE, "w") as f:
        f.write("\n".join(sorted(list(used)[-200:])))


def main():
    os.makedirs(TMP_DIR, exist_ok=True)
    used = load_used()

    token = get_bot_token()
    print("Собираю мемы из каналов:", ", ".join("@" + c for c in CHANNELS))

    candidates = []
    for ch in CHANNELS:
        imgs = fetch_channel(ch)
        print(f"  @{ch}: {len(imgs)} картинок")
        for u in imgs:
            if u not in used:
                candidates.append(u)
        if candidates:
            # берём свежий (первый найденный), но не повторяем каналы подряд
            break

    if not candidates:
        print("Нет новых мемов (все уже были отправлены или каналы пустые).")
        return 0

    choice = candidates[0]
    dest = os.path.join(TMP_DIR, f"meme_{int(__import__('time').time())}.jpg")
    print(f"Качаю: {choice}")
    if not download(choice, dest):
        print("Ошибка скачивания картинки.")
        return 1

    ok, resp = send_photo(token, OWNER_CHAT_ID, dest)
    if ok:
        save_used(used, choice)
        print("Мем отправлен владельцу ✔")
        return 0
    else:
        print("Ошибка отправки:", resp)
        return 1


if __name__ == "__main__":
    sys.exit(main())
