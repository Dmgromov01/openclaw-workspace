# OpenClaw Workspace

Личное рабочее пространство OpenClaw-агента (main). Содержит скрипты, заметки и интеграции.

> 🔒 Это **приватный** репозиторий. Секреты (токены, сессии, 2FA) в него **не попадают** — исключены через `.gitignore`.

## Структура

- **`calendar/`** — календарь и Telegram-логика (`gcal_reader.py`, `digest.py`, `bot_sender.py`)
- **`services/`** — systemd-шаблоны и watchdog (хаб, gateway, диск)
- **`docs/PROMPT-run6.md`** — промпт агенту main: gateway как system-юнит, без апрувов exec
- **`memory/`** — дневники сессий, `MEMORY.md` — долгосрочная память
- **`AGENTS.md`, `SOUL.md`, `IDENTITY.md`, `USER.md`, `TOOLS.md`, `HEARTBEAT.md`, `STATE.md`** — поведение агента

## Календарь (GOOGLE, чтение)

```bash
python3 calendar/gcal_reader.py today
python3 calendar/gcal_reader.py week
python3 calendar/gcal_reader.py list --days N
```

Подробнее — `STATE.md`.

## Секреты и модели

- Секреты вне репо (`.env`, `openclaw.json`).
- Чат: DeepSeek V4 Flash. Фото: DeepSeek Vision. Генерация: OpenRouter Gemini Flash. Google не использовать как LLM/vision.

## Сервисы (вне репо)

- `openclaw-gateway` — после run6 **system**-юнит, 127.0.0.1:18789. Рестарт: `systemctl restart openclaw-gateway`.
- `r2d2-hub` — хаб https://hub.gbkz.uk (:8091). Код в Dmgromov01/atlas-green-pearl-dawn, здесь не править.
- `telegram-user-svc` — 127.0.0.1:8765.
- Watchdog шлюза: `services/loop-watchdog-cron.sh` (алерты @HubAlertsbot).
