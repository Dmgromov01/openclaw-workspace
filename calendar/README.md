# Интеграция с календарём

> Канон: [`../STATE.md`](../STATE.md). Агент ходит в Google Calendar API (user OAuth). iCloud у агента нет.

## Google Calendar user OAuth

`gcal_reader.py` — календарь `dmgromov03@gmail.com`, Europe/Moscow.

- OAuth client: `/root/.openclaw/credentials/gcal/oauth-client.json`
- Refresh token: `/root/.openclaw/credentials/gcal/tokens.json`
- Просмотр: `python3 gcal_reader.py today`, `week`, `list --days N`
- Создание: `python3 gcal_reader.py add "<summary>" "<YYYY-MM-DDTHH:MM>" ["<end>"] --location "..." --description "..."`
- Удаление через этот CLI не реализовано.

Consent screen в Google Cloud должен быть **Production**. В Testing refresh-токен живёт ~7 дней.

Хаб (`atlas-green-pearl-dawn`) имеет отдельный Google OAuth в PGLite. Не путать с `tokens.json` агента.
