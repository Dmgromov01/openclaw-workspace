# OpenClaw Workspace

Личное рабочее пространство OpenClaw-агента (main). Содержит скрипты, заметки и интеграции.

> 🔒 Это **приватный** репозиторий. Секреты (api_id/api_hash, 2FA-пароли, токены, телефоны, сессии) в него **не попадают** — вычищены при первом коммите, исключены через `.gitignore`.

## Структура

- **`calendar/`** — календарь и Telegram-логика:
  - `icloud_calendar.py` — операции с календарём iCloud (Home): add/today/week/month/delete
  - `command_parser.py` — парсер команд «действие + дата + время + @ник»
  - `orchestrator.py` — связка парсер → календарь → .ics → отправка в Telegram
  - `digest.py` — сбор дайджеста (новости + курс валют)
  - `gcal_reader.py` — чтение Google Calendar
  - `ics_generator.py` — генерация .ics-приглашений
  - `tg_sender.py` — отправка через личный Telegram (Telethon, proxy)
  - `bot_sender.py` — отправка через бота @Dmbotmy_bot
  - `image_gen.py` — генерация картинок без ключа (Pollinations/Flux)
- **`memory/`** — дневники сессий (сырые логи), `MEMORY.md` — курируемая долгосрочная память.
- **`AGENTS.md`, `SOUL.md`, `IDENTITY.md`, `USER.md`, `TOOLS.md`, `HEARTBEAT.md`** — документы самоидентификации и поведения агента.

## Быстрый старт (календарь)

```bash
# Добавить встречу
python3 calendar/icloud_calendar.py add "позвонить Иванову" "15.08.2026 14:00"

# Расписание
python3 calendar/icloud_calendar.py today   # сегодня
python3 calendar/icloud_calendar.py week    # неделя
python3 calendar/icloud_calendar.py month   # месяц

# Удалить
python3 calendar/icloud_calendar.py delete --search "часть названия"
```

Подробнее — `calendar/README.md`.

## Конфигурация и секреты

- Секреты подтягиваются из окружения/файлов вне репозитория (`.env`, `config.json`, `openclaw.json`) — в коде захардкоженных значений нет.
- `.gitignore` исключает: `.env*`, `.session`, токены, `media/`, `_trash_/`, `tg-mtproto/`, `openclaw-workspace-state.json`, `node_modules/`.
- Модель по умолчанию: `deepseek/deepseek-chat` (DeepSeek V4 Flash, прямой API).

## Связанные сервисы (вне репо)

- `telegram-user-svc` — HTTP-сервис личного Telegram (systemd): `/auth/status`, `/send`, `/dialogs`, `/history`.
- Xray/VPN для обхода региональных ограничений (Telegram API).
- Корневые автоматизации: `daily-digest`, `server-check` (через OpenClaw cron).
