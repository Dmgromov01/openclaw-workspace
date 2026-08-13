# Интеграция с календарём (OpenClaw)

> ⚠️ **Актуальный календарь — GOOGLE CALENDAR API** (переехали с iCloud 10-11.08).
> `icloud_calendar.py` — устаревший legacy. Актуальный скрипт чтения — `gcal_reader.py`.

## Актуально: чтение Google Calendar
`/root/.openclaw/workspace/calendar/gcal_reader.py` (service-account, `dmgromov03@gmail.com`)

### Посмотреть расписание (Google)
- Сегодня: `python3 gcal_reader.py today`
- Неделя: `python3 gcal_reader.py week`
- N дней: `python3 gcal_reader.py list --days N`
- Дата/время — Europe/Moscow.

⚠️ Добавление/удаление событий на Google пока НЕ реализовано (gcal_reader только читает).

## Устаревшее (iCloud, legacy)
Формат запроса пользователя был: «действие + дата + время с годом».
Примеры: «позвонить Иванову 15.08.2026 14:00», «встреча с клиентом 20.08.2026 10:30».
```
python3 icloud_calendar.py add "<summary>" "<DD.MM.YYYY HH:MM>" [minutes]
python3 icloud_calendar.py today|week|month
python3 icloud_calendar.py delete --search "<часть названия>"
```
Был календарь Home из `ICLOUD_CALENDAR_URL` в `/root/tg_bot/.env`. Старый бот `bot.py` ОТКЛЮЧЁН.

## Автоматизации (cron)
- `daily-digest` — ежедневно 09:00 MSK, дайджест новостей + курс валют → Telegram 1916536646
- `server-check` — ежедневно 10:00 MSK, проверка основного сервера + WSS → Telegram 1916536646
- Новые автоматизации создавать через: `openclaw cron add --name X --cron "..." --tz Europe/Moscow --channel telegram --to telegram:1916536646 --announce --expect-final --message "..."`
