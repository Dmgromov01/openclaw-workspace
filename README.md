# OpenClaw Workspace

Личное рабочее пространство OpenClaw-агента (main). Содержит скрипты, заметки и интеграции.

> 🔒 Это **приватный** репозиторий. Секреты (api_id/api_hash, 2FA-пароли, токены, телефоны, сессии) в него **не попадают** — вычищены при первом коммите, исключены через `.gitignore`.

## Структура

- **`calendar/`** — календарь и Telegram-логика:
  - `gcal_reader.py` — **актуальный** календарь (Google Calendar API, чтение today/week/list)
  - `icloud_calendar.py` — УСТАРЕЛ (старая система iCloud, остался legacy; см. STATE.md)
  - `command_parser.py` — парсер команд «действие + дата + время + @ник»
  - `orchestrator.py` — связка парсер → календарь → .ics → отправка в Telegram
  - `digest.py` — сбор дайджеста (новости + курс валют)
  - `ics_generator.py` — генерация .ics-приглашений
  - `tg_sender.py` — отправка через личный Telegram (Telethon, proxy)
  - `bot_sender.py` — отправка через бота @Dmbotmy_bot
  - `image_gen.py` — генерация картинок без ключа (Pollinations/Flux)
- **`memory/`** — дневники сессий (сырые логи), `MEMORY.md` — курируемая долгосрочная память.
- **`AGENTS.md`, `SOUL.md`, `IDENTITY.md`, `USER.md`, `TOOLS.md`, `HEARTBEAT.md`** — документы самоидентификации и поведения агента.

## Быстрый старт (календарь — GOOGLE, чтение)

```bash
# Расписание (Google Calendar, актуально)
python3 calendar/gcal_reader.py today   # сегодня
python3 calendar/gcal_reader.py week    # неделя
python3 calendar/gcal_reader.py list --days N

# ⚠️ Добавление/удаление событий на Google пока НЕ реализовано (gcal_reader читает).
# Старый icloud_calendar.py (add/delete) — legacy от iCloud, не использовать как основной.
```

Подробнее — `calendar/README.md` и `STATE.md` (актуальное состояние).

## Конфигурация и секреты

- Секреты подтягиваются из окружения/файлов вне репозитория (`.env`, `config.json`, `openclaw.json`) — в коде захардкоженных значений нет.
- `.gitignore` исключает: `.env*`, `.session`, токены, `media/`, `_trash_/`, `tg-mtproto/`, `openclaw-workspace-state.json`, `node_modules/`.
- Модель по умолчанию: `deepseek/deepseek-chat` (DeepSeek V4 Flash, прямой API).

## Связанные сервисы (вне репо)

- `telegram-user-svc` — HTTP-сервис личного Telegram (systemd): `/auth/status`, `/send`, `/dialogs`, `/history`.
- Xray/VPN для обхода региональных ограничений (Telegram API).
- Корневые автоматизации: `daily-digest`, `server-check` (через OpenClaw cron).
