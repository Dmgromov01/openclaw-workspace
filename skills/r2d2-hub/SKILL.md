# R2D2 Hub — перенос и правила

Используй, когда Дмитрий просит: Mini App, R2D2, хаб, админку, OpenClaw в мини-апп, BYOK, PIN, порт с Grok.

Читай сначала этот файл, потом `INSTALL.md`. Промпт для старта — `PROMPT.md`.

## Два мира (не путать)

1. **Сейчас на VPS** — Python Mini App (`miniapp/server.py` + `auth.py` + `static/index.html`), systemd `miniapp.service`, наружу только через nginx префикс `/miniapp/`.
2. **Grok-превью** — полная пересборка (хаб + HMAC + PIN + BYOK + админка + квоты). Исходник **не в этом репо**, пока Дмитрий не скажет залить его на GitHub.

Не ломай работающий Python, пока фаза 2 не пройдёт смоук. Откат: старый юнит + старый `сtatic/index.html`.

## Правила (железо)

- HMAC initData: `secret = HMAC-SHA256(key="WebAppData", msg=bot_token)`, replay `auth_date` ≤ 24ч, `compare_digest`.
- Токен сессии: `secrets.token_urlsafe(32)`, в БД только **SHA-256 хеш**, TTL 7 дней.
- PIN 4–8 цифр, **scrypt** (не SHA256(salt+password)). Пароль-заглушку из фронта убрать.
- Владелец = telegram_id из `TELEGRAM_OWNER_ID` (не хардкод). Его нельзя разжаловать/блокировать/удалить. Нельзя снять последнего админа.
- BYOK: AES-256-GCM, в UI только хвост ключа. Общий AI — только если админ включил + дневная квота до запроса.
- OpenClaw gateway — OpenAI-compatible `POST /v1/chat/completions`. Не светить токен шлюза в репо и в MEMORY.md.
- Источники RSS только https, без внутренних IP, лимит 12.
- Не копировать OAuth Google и calendar id в мини-апп. Календарь остаётся `calendar/gcal_reader.py`.
- Не коммитить `.env`, токены, `miniapp.db`, прототипы v2–v18, вендоренный Sphinx docs.
- Перед systemd/nginx: прочитать текущее, merge, бэкап, спросить Дмитрия.
- Превью без Telegram должно открываться (устройство-сессия или PIN).

## Что не делать

- Не ставить Node-хаб поверх Python, пока исходник не в GitHub и нет смоука.
- Не собирать Vite на 2GB, если уже жмёт OpenClaw — сборка либо с swap, либо артефакт приходит готовый.
- Не тянуть Grok Better Auth / connectors — Telegram HMAC наш.
