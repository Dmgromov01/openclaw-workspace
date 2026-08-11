#!/usr/bin/env python3
"""Бесплатная генерация картинок через Pollinations (без ключа).
Использование:
    python3 image_gen.py "кот в скафандре"
    python3 image_gen.py "мем: кот недоумевает, подпись 'опросы'" --size 1024x1024
    python3 image_gen.py "..." --send  # отправить владельцу в Telegram
"""
import argparse, base64, io, os, re, sys, time, urllib.parse, urllib.request

OWNER_CHAT_ID = "1916536646"


def get_bot_token():
    """Токен бота из конфига OpenClaw."""
    path = "/root/.openclaw/openclaw.json"
    import json
    with open(path) as f:
        cfg = json.load(f)
    # ищем botToken в channels.telegram
    ch = cfg.get("channels", {}).get("telegram", {})
    tok = ch.get("botToken")
    if not tok:
        # fallback: любой ключ-значение с 'botToken' или 'token'
        def walk(o):
            if isinstance(o, dict):
                if "botToken" in o and isinstance(o["botToken"], str):
                    return o["botToken"]
                for v in o.values():
                    r = walk(v)
                    if r:
                        return r
            elif isinstance(o, list):
                for v in o:
                    r = walk(v)
                    if r:
                        return r
        tok = walk(cfg)
    return tok


def send_photo(photo_bytes_or_path, caption=""):
    """Отправляет фото владельцу через Bot API."""
    token = get_bot_token()
    if not token:
        print("НЕТ ТОКЕНА для отправки")
        return False
    if isinstance(photo_bytes_or_path, str) and os.path.exists(photo_bytes_or_path):
        files = {"photo": open(photo_bytes_or_path, "rb")}
    else:
        files = {"photo": ("image.jpg", photo_bytes_or_path, "image/jpeg")}
    data = {"chat_id": OWNER_CHAT_ID, "caption": caption}
    req = urllib.request.Request(
        f"https://api.telegram.org/bot{token}/sendPhoto",
        data=urllib.parse.urlencode(data).encode() if not files else data,
    )
    # multipart нужен для файлов
    try:
        boundary = "----clawboundary" + str(int(time.time() * 1000))
        if isinstance(photo_bytes_or_path, bytes):
            body = io.BytesIO()
            for k, v in data.items():
                if not v:
                    continue
                body.write(f"--{boundary}\r\nContent-Disposition: form-data; name=\"{k}\"\r\n\r\n{v}\r\n".encode())
            fname = "image.jpg"
            body.write(f"--{boundary}\r\nContent-Disposition: form-data; name=\"photo\"; filename=\"{fname}\"\r\nContent-Type: image/jpeg\r\n\r\n".encode())
            body.write(photo_bytes_or_path)
            body.write(f"\r\n--{boundary}--\r\n".encode())
            payload = body.getvalue()
            headers = {"Content-Type": f"multipart/form-data; boundary={boundary}", "Content-Length": str(len(payload))}
            req = urllib.request.Request(f"https://api.telegram.org/bot{token}/sendPhoto", data=payload, headers=headers, method="POST")
        else:
            # файл на диске
            with open(photo_bytes_or_path, "rb") as fimg:
                payload = fimg.read()
            from email.parser import BytesParser
            mp = io.BytesIO()
            for k, v in data.items():
                if not v:
                    continue
                mp.write(f"--{boundary}\r\nContent-Disposition: form-data; name=\"{k}\"\r\n\r\n{v}\r\n".encode())
            fname = os.path.basename(photo_bytes_or_path)
            mp.write(f"--{boundary}\r\nContent-Disposition: form-data; name=\"photo\"; filename=\"{fname}\"\r\nContent-Type: image/jpeg\r\n\r\n".encode())
            mp.write(payload)
            mp.write(f"\r\n--{boundary}--\r\n".encode())
            payload = mp.getvalue()
            headers = {"Content-Type": f"multipart/form-data; boundary={boundary}", "Content-Length": str(len(payload))}
            req = urllib.request.Request(f"https://api.telegram.org/bot{token}/sendPhoto", data=payload, headers=headers, method="POST")
        resp = urllib.request.urlopen(req, timeout=60)
        print(f"Отправлено владельцу ✔ ({resp.status})")
        return True
    except Exception as e:
        print(f"Ошибка отправки: {e}")
        return False


def generate(prompt, size="512x512", model="flux"):
    """Генерирует картинку через Pollinations, возвращает байты."""
    # модель: flux / turbo / etc
    p = urllib.parse.quote(prompt)
    url = (
        f"https://image.pollinations.ai/prompt/{p}"
        f"?width={size.split('x')[0]}&height={size.split('x')[1]}&nologo=true&model={model}&seed={int(time.time())}"
    )
    print(f"Генерирую: {prompt[:60]}... ({size}, {model})")
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=120) as r:
        data = r.read()
    print(f"Готово: {len(data)} байт")
    return data


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("prompt", nargs="+")
    ap.add_argument("--size", default="512x512")
    ap.add_argument("--model", default="flux")
    ap.add_argument("--send", action="store_true", help="отправить владельцу в Telegram")
    ap.add_argument("--out", default="/root/.openclaw/workspace/calendar/generated.jpg")
    a = ap.parse_args()
    prompt = " ".join(a.prompt)
    data = generate(prompt, a.size, a.model)
    with open(a.out, "wb") as f:
        f.write(data)
    print(f"Сохранено: {a.out}")
    if a.send:
        send_photo(a.out, prompt)
    # печатаем путь для агента (медиа-вложение)
    print(f"OUT:{a.out}")


if __name__ == "__main__":
    main()
