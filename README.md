<!-- project: github.com/Dmgromov01/openclaw-workspace -->
# OpenClaw Workspace

Личное рабочее пространство OpenClaw-агента. Репозиторий приватный; секреты, сессии и runtime credentials хранятся вне git.
Канон живой инфры: STATE.md. Не читать docs/archive/ как конфиг.

## Структура

`calendar/` содержит календарь, дайджест и Telegram-логику. `bot/` содержит безопасный приём документов и доставку отчётов. `services/` содержит systemd-шаблоны и watchdog-скрипты. `skills/` и `openclaw_modules/` содержат инструменты анализа данных. `plugins/` содержит интеграции OpenClaw, а `tests/` — автономные проверки утилит.

## Проверка перед отправкой изменений

В окружении с зависимостями проекта выполните:

```bash
python3 -m compileall -q bot calendar services skills openclaw_modules
python3 -m pytest -q
node --check plugins/jina-tools/jina-core.js
node --check plugins/jina-tools/index.js
```

Тесты, которым нужны необязательные runtime-зависимости (aiogram, Telethon, Google API или DuckDB), должны импортировать модуль лениво либо запускаться в полном production-окружении.

## Календарь

Актуальный календарь — Google Calendar API в часовом поясе Europe/Moscow:

```bash
python3 calendar/gcal_reader.py today
python3 calendar/gcal_reader.py week
python3 calendar/gcal_reader.py list --days N
python3 calendar/gcal_reader.py add "<summary>" "<YYYY-MM-DDTHH:MM>" ["<end>"] --location "..." --description "..."
```

Команда `add` требует OAuth-права календаря на чтение и запись. Удаление событий через этот CLI не реализовано. Секреты Google должны оставаться в runtime-путях, перечисленных в `calendar/gcal_reader.py`, и не добавляться в git.

## Telegram

Операторский бот: @Dmbotmy_bot → агент main.
Пейджер хаба: @HubAlertsbot (токен только в .env хаба, не здесь).

Отправка из workspace CLI: calendar/bot_sender.py
(токен через services.digest.secrets.read_secret_ref, TG_OWNER_CHAT_ID).
calendar/tg_sender.py и calendar/ics_generator.py перенесены в
archive/2026-08-31/calendar/ — не живой путь, не cron, не импортировать.

bot/file_handler.py ограничивает документы расширениями .xlsx .xls .csv .pdf,
размером 25 МБ, безопасным именем и уникальным путём. Динамический текст
экранируется перед Telegram HTML.

## Дайджест и внешние сервисы

Дайджест использует RSS, публичные страницы Telegram и DeepSeek. Секреты читаются из runtime-конфигурации через `services/digest/secrets.py`; ключи не должны попадать в логи или исходный код. `plugins/jina-tools/jina_search` обращается к Jina Search. `jina_rag` передаёт выбранные фрагменты файлов во внешний Jina API и по умолчанию отключён; для явного разрешения нужен `JINA_RAG_ALLOW_EXTERNAL=1`. RAG ограничивает число файлов, размер файлов, число чанков и размер результата.

## Сервисы

Gateway, hub и Telegram service должны оставаться привязанными к loopback согласно `STATE.md`. Перед изменением systemd, cron или nginx сначала проверьте фактическую конфигурацию на сервере. Не коммитьте токены, OAuth-файлы, Telethon-сессии, базы данных или runtime-кэш.
