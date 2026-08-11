# Интеграция с календарём iCloud (OpenClaw)

## Скрипт
`/root/.openclaw/workspace/calendar/icloud_calendar.py`

## Доступные операции

### Добавить встречу
Формат запроса пользователя: «действие + дата + время с годом».
Примеры:
- «позвонить Иванову 15.08.2026 14:00»
- «встреча с клиентом 20.08.2026 10:30»
- «завтра в 10:00 позвонить клиенту»
- «купить молоко 21.08.2026 9:00»

Команда:
```
python3 icloud_calendar.py add "<summary>" "<DD.MM.YYYY HH:MM>" [minutes]
```
Пример:
```
python3 icloud_calendar.py add "позвонить Петрову" "18.08.2026 11:30"
```
(по умолчанию 60 минут)

### Посмотреть расписание
- Сегодня: `python3 icloud_calendar.py today`
- Неделя: `python3 icloud_calendar.py week`
- Месяц: `python3 icloud_calendar.py month`
- N дней: `python3 icloud_calendar.py list --days N`

### Удалить встречу
- По названию: `python3 icloud_calendar.py delete --search "<часть названия>"`
- За конкретную дату: `python3 icloud_calendar.py delete --date "DD.MM.YYYY"`

## Важно
- Календарь: **Home** (основной), из `ICLOUD_CALENDAR_URL` в `/root/tg_bot/.env`.
- Дата/время — в Europe/Moscow.
- Старый бот `bot.py` ОТКЛЮЧЁН (Вариант А). Конфликт токенов решён.
- Дубли встреч больше не создаются — парсер чистит служебные слова и пишет в конкретный календарь.

## Автоматизации (cron)
- `daily-digest` — ежедневно 09:00 MSK, дайджест новостей + курс валют → Telegram 1916536646
- `server-check` — ежедневно 10:00 MSK, проверка сервера 5.181.108.40 + WSS → Telegram 1916536646
- Новые автоматизации создавать через: `openclaw cron add --name X --cron "..." --tz Europe/Moscow --channel telegram --to telegram:1916536646 --announce --expect-final --message "..."`
