# Установка R2D2 Hub на этом хосте

Делай **по фазам**. Каждую фазу закрывай записью в `STATE.md` и `memory/YYYY-MM-DD.md`.

## Фаза 0 — подтянуть этот скилл

1. `git pull` рабочего репо (ветка `r2d2-hub-port` или `main` после мержа).
2. Прочитать `skills/r2d2-hub/SKILL.md`.
3. Не трогать nginx/systemd, пока Дмитрий не написал «ставь фазу 1».

## Фаза 1 — патчи текущего Python (без смены стека)

Цель: работающий хаб остаётся Python, но по правилам из SKILL.md.

Сделать в `miniapp/auth.py` и `miniapp/server.py`:

1. Сессии: хранить `sha256(token)`, не plaintext.
2. PIN/пароль: scrypt или PBKDF2 ≥ 100k; убрать `sha256(salt+password)`.
3. `OWNER_TG_ID` читать из env `TELEGRAM_OWNER_ID`, fallback только если env пуст.
4. Защита владельца + последнего админа. DELETE user как сейчас, logout инвалидирует сессию.
5. Убрать захардкоженный стартовый пароль генератора в `static/index.html`.
6. AI: не DeepSeek напрямую из мини-аппа. Прокси на OpenClaw gateway (`OPENCLAW_GATEWAY_URL`, токен из env). Квота на пользователя до вызова.
7. BYOK: ключ шифруется AES-256-GCM, мастер из `AI_KEY_SECRET` или bot token. SSRF: только https, не private IP.
8. Админка: allowed, role, allow_global_ai, quota_daily, удаление, аудит.
9. Перезапустить `miniapp.service`. Смоук: `/miniapp/` отдаёт HTML, `/miniapp/api/auth/me` без токена — 401.

Env (уже есть в openclaw `.env`, **не коммитить**):

- `TELEGRAM_BOT_TOKEN` — обязателен (HMAC).
- `TELEGRAM_OWNER_ID` — проставить, если нет.
- `OPENCLAW_GATEWAY_URL` — локальный шлюз агента.
- `OPENCLAW_GATEWAY_TOKEN` — если шлюз требует.
- `AI_KEY_SECRET` — отдельная строка для AES, не равнать bot token навсегда.

## Фаза 2 — Node-хаб (только когда исходник на GitHub)

Срабатывает, когда появится репо вроде `Dmgromov01/r2d2-hub` или папка `hub/` в этом workspace.

1. Не трогать текущий Python. Клон рядом: `/root/openclaw/hub`.
2. Node 22 LTS. `npm ci` / `npm i`, `npm run build`. Если OOM — сначала swap, иначе сказать Дмитрию: сборка тяжёлая для 2GB.
3. `base` приложения должен быть `/miniapp/` (сейчас бот и nginx ждут этот префикс). Корень `/` — это OpenClaw gateway, **не** хаб.
4. База: SQLite/PGLite рядом с хабом. Не тащить `miniapp.db` Python.
5. systemd `hub.service` на loopback, другой порт, чем Python. nginx: временно `/miniapp-next/` → Node. Смоук в Telegram WebApp и в браузере.
6. Когда Дмитрий ок — переключить `/miniapp/` на Node, Python оставить как `miniapp-legacy.service` 48ч.
7. Погодные JPG можно взять из `miniapp/static/weather-assets/`, не тащить бинарники в git, если уже есть на диске.

## Фаза 3 — память агента

После успеха обнови:

- `STATE.md` — Mini App = что реально служит (стек, префикс, админка).
- `MEMORY.md` — урок: сессии хеш, не plaintext; владелец из env; AI через gateway.
- `AGENTS.md` — одна строка-ссылка на `skills/r2d2-hub/SKILL.md`.
- `USER.md` — Дмитрий, Europe/Moscow, хаб R2D2.
- Не писать токены, IP, Tailscale в новые файлы.
