#!/usr/bin/env python3
"""Анимация одной картинки через OpenRouter /videos (image-to-video).

Запуск:
  OPENROUTER_API_KEY=<ключ> python3 scripts/make_video.py [картинка] [выход.mp4]
"""
import base64
import json
import os
import sys
import time
import urllib.request

IMG = sys.argv[1] if len(sys.argv) > 1 else (
    "/root/openclaw/media/inbound/openclaw-staged-cf283769-37fe-4e55-b86e-14901c87eaa3/"
    "input-c3743168-3f2c-4470-9f15-972e966cb6d6.jpg"
)
OUT = sys.argv[2] if len(sys.argv) > 2 else "/root/openclaw/birthday-card.mp4"
MODEL = os.environ.get("OR_VIDEO_MODEL", "google/veo-3.1-lite")
PROMPT = os.environ.get(
    "OR_VIDEO_PROMPT",
    "Оживи поздравительную открытку: бордер-колли в синем цилиндре, серый кот на "
    "одноколесном велосипеде и пёс в жёлтой бабочке в горошек на цирковой арене. "
    "Плавное движение камеры, лёгкое покачивание, конфетти, праздничная атмосфера. "
    "Лица и надписи не менять.",
)

KEY = os.environ.get("OPENROUTER_API_KEY")
if not KEY:
    sys.exit("Нет OPENROUTER_API_KEY в окружении — запусти с ключом в переменной.")
if not os.path.exists(IMG):
    sys.exit("Картинка не найдена: " + IMG)

ext = IMG.rsplit(".", 1)[-1].lower()
mime = "image/png" if ext == "png" else "image/jpeg"
with open(IMG, "rb") as fh:
    b64 = base64.b64encode(fh.read()).decode()

payload = {
    "model": MODEL,
    "prompt": PROMPT,
    "frame_images": [
        {
            "type": "image_url",
            "image_url": {"url": "data:%s;base64,%s" % (mime, b64)},
            "frame_type": "first_frame",
        }
    ],
    "resolution": "1080p",
    "aspect_ratio": "16:9",
    "generate_audio": False,
}


def call(url, data=None):
    headers = {"Authorization": "Bearer " + KEY}
    body = None
    if data is not None:
        body = json.dumps(data).encode()
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=body, headers=headers)
    return json.load(urllib.request.urlopen(req, timeout=180))


job = call("https://openrouter.ai/api/v1/videos", payload)
polling = job.get("polling_url")
print("job:", job.get("id"), "status:", job.get("status"))
if not polling:
    sys.exit("Нет polling_url в ответе: " + json.dumps(job)[:500])

while True:
    time.sleep(8)
    st = call(polling)
    state = st.get("status")
    print("status:", state)
    if state in ("completed", "succeeded"):
        urls = st.get("unsigned_urls") or []
        if not urls:
            sys.exit("Готово, но нет unsigned_urls: " + json.dumps(st)[:500])
        with urllib.request.urlopen(urls[0], timeout=600) as resp, open(OUT, "wb") as fh:
            fh.write(resp.read())
        print("saved:", OUT)
        break
    if state in ("failed", "error"):
        sys.exit("Генерация упала: " + json.dumps(st)[:600])
