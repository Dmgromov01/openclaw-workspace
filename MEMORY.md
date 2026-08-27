# MEMORY.md — Долгосрочная память

Свёрнуто 27.08.2026: файл обрезался (26k > 20k). Дневники — `memory/YYYY-MM-DD.md`. Живое состояние — `STATE.md`.

## Кто мой человек
- **Дмитрий** (@Dm_GRM), tg **1916536646**. Бот оператора: **@Dmbotmy_bot** → агент **main**.
- Машина: **hiplet-112102**, Ubuntu 24.04, RAM ~3.8G, zram0 ~2G, tailnet tail6a4baa. IP 138.124.180.178 (Франкфурт). Старые хосты (hiplet-109548, vps-7182, 2 GB RAM) — не путать.
- iPhone сопряжён как node. Подключение: `openclaw qr --url wss://gbkz.uk` (код настройки), порт **443** через nginx, не 18789. auth.mode=token, не password.

## Неприкосновенное
- НЕ править руками `openclaw.json` / credentials. Конфиг — `openclaw config set` только по прямому ТЗ хозяина, не сам.
- НЕ рестартить gateway из Telegram. Шлюз = **system**-юнит `openclaw-gateway`. Команда с SSH: `systemctl restart openclaw-gateway`. User-юнит снесён, linger выкл. Не ставить второй gateway.
- НЕ трогать: код хаба, ufw, zram, Parallel, Context7, GitHub MCP, агент hub (`tools.allow=[]`).
- Exec: `mode=allowlist`, ask=off, без /approve. Не security=full. Не добавлять в allowlist: rm reboot systemctl loginctl systemd-run chmod chown ufw.
- Mini App выключен, :8080 не слушает. Кнопка в боте = ссылка https://hub.gbkz.uk (не BotFather Mini App).

## Принципы Дмитрия
- В Telegram — **только результат**, без «сейчас сделаю» и логов.
- Думать о **намерении**, не исполнять буквально. Если уже сделано — не переделывать. Дорогое/массовое — один уточняющий вопрос.
- Изменения workspace — `git commit` + `git push`. Секреты в git не класть.
- В прод без явного «можно» — ничего. Тестовый второй gateway на этом хосте не поднимать (столкнётся на :18789).

## Модели (27.08)
- Чат / heartbeat: `deepseek/deepseek-v4-flash`
- Глубоко: `deepseek/deepseek-v4-pro` (не делать дефолтом)
- Входящее фото: `deepseek/deepseek-v4-flash-vision-exp` через прямой DeepSeek. Не Google, не `openclaw media`.
- Генерация с нуля: Pollinations `python3 calendar/image_gen.py "<prompt>" [w] [h]`. `image_generate` — только ретушь/высокое качество (OpenRouter → Gemini Flash image).
- Не возвращать Google как LLM/vision/fallback. Календарь хаба (gcal) — это другое, не трогать.

## Домены
- **gbkz.uk** — основной. Cloudflare → nginx TLS → 127.0.0.1:18789. WSS wss://gbkz.uk. Серт до 17.11.2026 (certbot.timer).
- **hub.gbkz.uk** — сайт хаба, nginx → :8091, systemd `r2d2-hub`. Код хаба не трогать.
- **dmkz.org** — заброшен (Timeweb), не использовать.
- Креды R2/Cloudflare: `/root/.openclaw/credentials/cloudflare/r2.json` (chmod 600, вне git).

## Календарь = Google, не iCloud
- `calendar/gcal_reader.py` + SA `/root/.openclaw/credentials/gcal/`. Команды: today / week / list --days N. Europe/Moscow.
- Google API пока только читает. iCloud-скрипты удалены.
- Кнопки расписания → gcal_reader, в чат только `• ДД.ММ.ГГГГ ЧЧ:ММ — summary`.

## Дайджест
- Кнопка «Дайджест» = `calendar/digest.py` (РБК, Коммерсантъ, Медуза, Важные истории, The Bell, BAZA + курс ЦБ). НЕ web_search, НЕ Google News, НЕ расписание.
- Блоки **по источникам**, не по темам. Обрезка только по целому слову. Ключ DeepSeek — из openclaw.json, не печатать.

## telegram-user-svc
- systemd `telegram-user-svc`, HTTP 127.0.0.1:8765, authorized = Дмитрий. pkill по server.py не использовать — юнит сам поднимет.
- Плагин tg-user-tools: tg_send, tg_send_file, tg_dialogs, tg_history.

## WhatsApp
- Закрыт, не возвращаться без явного запроса.

## Уроки
- Два gateway (user + system) на :18789 = мёртвый бот. User снесён 27.08.
- `openclaw config set` посреди сессии → reload → шлюз падает. Не крутить конфиг самому.
- Не добавлять модель в primary до каталога провайдера.
- DeepSeek id: `deepseek-chat` и `deepseek-reasoner` оба → v4-flash.
- Компакция: `keepRecentTokens` держать выше пика диалога, иначе overflow → already_compacted → бот «мёртв».

## Хвосты
1. Дайджест @de574574 — по необходимости.
2. Face ID / инвайты хаба — не делались.
3. `gateway.reload.mode=off` — выставить с SSH, не через бота.
