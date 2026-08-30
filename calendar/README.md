# Интеграция с календарём

> Канон runtime-состояния: [`../STATE.md`](../STATE.md). Актуальный календарь агента — Google Calendar API; iCloud-скрипты являются legacy.

## Google Calendar user OAuth

`gcal_reader.py` работает с календарём `dmgromov03@gmail.com` в часовом поясе Europe/Moscow.

- OAuth client: `/root/.openclaw/credentials/gcal/oauth-client.json`
- Refresh token: `/root/.openclaw/credentials/gcal/tokens.json`
- Команды просмотра: `python3 gcal_reader.py today`, `python3 gcal_reader.py week`, `python3 gcal_reader.py list --days N`.
- Создание: `python3 gcal_reader.py add "<summary>" "<YYYY-MM-DDTHH:MM>" ["<end>"] --location "..." --description "..."`.
- Удаление через этот CLI не реализовано.

OAuth consent screen должен быть опубликован владельцем в Google Cloud Console. Пока приложение находится в Testing, refresh tokens могут истекать примерно через 7 дней.

## Legacy iCloud

`icloud_calendar.py` и iCloud-код hub не использовать для новых работ. Их удаление — отдельная миграция после проверки, что Google flow покрывает все нужные сценарии.
