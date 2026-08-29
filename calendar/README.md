# Интеграция с календарём (OpenClaw)

> Актуальный календарь — Google Calendar API (переезд с iCloud выполнен 10–11.08). `icloud_calendar.py` — устаревший legacy; актуальный скрипт — `gcal_reader.py`.

## Google Calendar

`/root/.openclaw/workspace/calendar/gcal_reader.py` работает с календарём `dmgromov03@gmail.com` в часовом поясе Europe/Moscow.

Команды просмотра: `python3 gcal_reader.py today`, `python3 gcal_reader.py week` и `python3 gcal_reader.py list --days N`.

Команда `add` создаёт событие: `python3 gcal_reader.py add "<summary>" "<YYYY-MM-DDTHH:MM>" ["<end>"] --location "..." --description "..."`. Для неё используются OAuth-права календаря на чтение и запись. Удаление событий через этот CLI не реализовано.

## Устаревший iCloud

Старые команды iCloud сохранены только как справочная legacy-документация:

```text
python3 icloud_calendar.py add "<summary>" "<DD.MM.YYYY HH:MM>" [minutes]
python3 icloud_calendar.py today|week|month
python3 icloud_calendar.py delete --search "<часть названия>"
```

Старый бот `bot.py` отключён.

## Автоматизации (cron)

`daily-digest` запускается ежедневно в 09:00 MSK, а `server-check` — ежедневно в 10:00 MSK. Новые автоматизации создавать через `openclaw cron add` с явно указанным часовым поясом `Europe/Moscow` и адресатом владельца.
