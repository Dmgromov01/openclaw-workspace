# STATE.md — актуальное runtime-состояние

> Это единственный канон для живой инфраструктуры. Перед изменением сверяйте его с SSH/runtime; исторические документы не являются источником конфигурации.

## Календарь — Google Calendar API
- Канал календаря: Google Calendar API, часовой пояс Europe/Moscow; iCloud не используется агентом.
- Агентский CLI: `calendar/gcal_reader.py` (`today`, `week`, `list --days N`, `add`).
- Авторизация: **user OAuth** — `/root/.openclaw/credentials/gcal/oauth-client.json` + `tokens.json`; это не service account.
- OAuth consent screen должен быть переведён владельцем из Testing в Production, иначе refresh-токены могут истекать через 7 дней.
- Hub пока содержит legacy iCloud-код; не считать его рабочим каноном и не удалять без отдельной миграции/проверки.

## Модели и память
- Обычный чат: `deepseek/deepseek-v4-flash`; глубокие задачи: `deepseek/deepseek-v4-pro`; фото: `deepseek/deepseek-v4-flash-vision-exp`.
- Не возвращать Google в LLM, vision или fallback. Google Calendar — отдельная интеграция.
- Builtin memory search: Jina `jina-embeddings-v3` через `https://api.jina.ai/v1`, provider `openai-compatible`.
- Memory sources: только `memory`; `sessionMemory=false`; `keepRecentTokens=80000`.
- Jina RAG требует явного `JINA_RAG_ALLOW_EXTERNAL=1`; embeddings не менять без прямого ТЗ.

## Инфраструктура
- Хост: `hiplet-112102`, Ubuntu 24.04, RAM ~3.8 GiB, zram ~2 GiB.
- OpenClaw gateway: system unit `openclaw-gateway`, `/root/openclaw`, loopback `127.0.0.1:18789`; не ставить user-unit и не запускать второй gateway.
- Hub: `r2d2-hub`, `/root/atlas-green-pearl-dawn/.output/server/index.mjs`, loopback `127.0.0.1:8091`, nginx → `https://hub.gbkz.uk`.
- Telegram user service: `telegram-user-svc`, `127.0.0.1:8765`.
- Mini App выключен, `:8080` не слушает. Кнопка бота ведёт на `https://hub.gbkz.uk`.
- UFW WAN: 22/80/443 + tailnet `100.64.0.0/10`; не менять без отдельного ТЗ.

## Guardrails
- Не править вручную `openclaw.json` или credentials: конфиг только `openclaw config set` по прямому ТЗ, затем `openclaw config validate`.
- Не рестартить gateway из Telegram; systemd/nginx/cron менять только после inspection, backup и явного разрешения.
- Exec main: allowlist, ask=off; не `security=full`; не добавлять destructive-команды в allowlist.
- Агент hub: `tools.allow=[]`; не включать инструменты без отдельного решения.
- GitHub remotes не должны содержать credentials/token в URL. Секреты, OAuth, sessions, runtime caches и personal reports не коммитить.

## Watchdog и backup
- Hub watchdog: cron каждую минуту, 3 провала → restart `r2d2-hub`.
- Gateway + tgsvc watchdog: `services/loop-watchdog-cron.sh`, антишторм 60 сек, алерты через HubAlertsbot.
- Backups: `/var/backups/r2d2`; latest archive restore-test прошёл в изолированном `/tmp`.
