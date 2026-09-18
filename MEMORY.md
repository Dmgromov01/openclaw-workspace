<!-- project: github.com/Dmgromov01/openclaw-workspace -->
# MEMORY.md — Долгосрочная память

## Кто мой человек
- Дмитрий; операторский бот `@Dmbotmy_bot` → main. Семейный сайт: `https://hub.gbkz.uk`.

## Неприкосновенное
- Без разрешения — никакой разработки: не создавать/менять задания, скрипты, конфиги, сервисы по своей инициативе. Сначала спросить.
- `openclaw.json`/credentials — только `openclaw config set` + validate по прямому ТЗ.
- Gateway — system unit и loopback; не создавать второй gateway.
- Hub agent `tools.allow=[]`; Google не возвращать в LLM/vision/fallback.

## Доступ пользователей

- Новые пользователи по умолчанию: restricted-профиль (агент `chat`), как у 8335493342 — НЕ main.
  Канон: allow=[read,write,edit,view_image,group:web], deny=[exec,process,message,cron,sessions_*,subagents,gateway,nodes,mcp,secrets,apply_patch,tool_search,tool_describe,tool_call], codeMode=false.
  Применять: `OPENCLAW_ACTOR_TG_ID=1916536646 /root/openclaw/bin/bot-access-operator enable-restricted <TG_ID>` (аргумент опционален; по умолчанию 8335493342). Не вручную в openclaw.json.

## Поиск (правило 2026-09-06)
- Базовый веб-поиск: `web_search` (провайдер `parallel-free`). searxng доступен возвратом: `openclaw config set tools.web.search.provider searxng`.
- Выбор по специфике задачи, а не «один на всё»: keenable (MCP) — семантический поиск с фильтрами site/даты/acquired; context7 — доки библиотек/API; github MCP — код/репо/issues; web_fetch — конкретный URL. Если инструмент релевантнее под специфику запроса — использовать его.

## Модели
- Чат и vision: **DeepSeek V4.1 Flash** (`deepseek/deepseek-flash`) — дефолт + image с 2026-09-10. Legacy-имена `deepseek-v4-flash` и `deepseek-v4-flash-vision-exp` обслуживаются той же V4.1 Flash. V4 Pro выводится: с 14.09.2026 запросы к `deepseek-v4-pro` маршрутизируются на V4.1 Flash. <!-- project: github.com/Dmgromov01/openclaw-workspace -->
- Image pipeline: перед обещанием генерации/редактирования сначала проверять, что в текущей сессии реально доступен image-generation tool и что входное вложение имеет разрешённый immutable attachment/path. Не выдумывать пути вроде `dog.jpg`; отсутствие image tool или референса = сразу честный отказ без запуска, повторных обещаний и лишнего Composio. После переключения модели/команды `/Models` capability-state может измениться, поэтому preflight обязателен на каждом image-turn. <!-- project: github.com/Dmgromov01/openclaw-workspace -->

## Провайдеры
- `relaymodels`: 403 `token quota is not enough, token remain quota: ...` = исчерпана **квота конкретного API-ключа**, а не баланс аккаунта (на аккаунте было 100 млн токенов, а ключ упирался в свой лимит). Gateway помечает это как `reason=auth` — не путать с auth-сбоем; рестарт/env/новый ключ не помогают, лечится поднятием лимита ключа в кабинете. Проверка вживую: `openclaw agent --agent main --model relaymodels/<model> --message "ping"`. <!-- project: github.com/Dmgromov01/openclaw-workspace -->

## Календарь
- Агент: Google user OAuth, `gcal_reader.py` today/week/list/add. Хаб: отдельный Google OAuth/PGLite flow. iCloud dormant.

## Урок 2026-08-31
- Старый skill хаба врал про Python Mini App; живой хаб — Node/Nitro `hub.gbkz.uk`.
- Дайджест и календарные уведомления не должны иметь параллельные cron-рассылки.
- Git без совпадающего `origin/main` не означает выполненную работу.
- Агент hub остаётся без tools; main остаётся операторским агентом.
- Runtime state, sessions и личные отчёты не коммитить.

## Promoted From Short-Term Memory (2026-09-02)

<!-- openclaw-memory-promotion:memory:memory/2026-08-27-run6.md:3:3 -->
- 2026-08-27 evening — run6 (Grok → GitHub, bot applies on the machine): Plan and files pushed to `Dmgromov01/openclaw-workspace`. Hub code not touched. [score=0.812 recalls=0 avg=0.620 source=memory/2026-08-27-run6.md:3-3]
<!-- openclaw-memory-promotion:memory:memory/2026-08-27-run6.md:6:9 -->
- Owner decision: Remove exec approvals for agent main (no more /approve buttons).; Gateway → system unit, linger root, watchdog :18789 and :8765.; Expand allowlist; outside list → deny without hanging. Not security=full.; Burn Google from LLM/vision. Photos = DeepSeek Vision. No CLI media. [score=0.812 recalls=0 avg=0.620 source=memory/2026-08-27-run6.md:6-9]
<!-- openclaw-memory-promotion:memory:memory/2026-08-27-run6.md:12:15 -->
- Files: `docs/PROMPT-run6.md` — prompt for the bot (paste whole into @Dmbotmy_bot); `docs/run6.md` — why; `services/openclaw-gateway.service` — system unit template; `services/loop-watchdog.sh` + `loop-watchdog-cron.sh` [score=0.812 recalls=0 avg=0.620 source=memory/2026-08-27-run6.md:12-15]
<!-- openclaw-memory-promotion:memory:memory/2026-08-27-run6.md:18:21 -->
- Exec: `tools.exec.mode=allowlist` (= security=allowlist + ask=off); `channels.telegram.execApprovals.enabled=false`; allowlist: ls cat head tail df journalctl date uname free zramctl mkdir mv tar gpg git ss curl openclaw; systemctl/loginctl — only for this run, then drop them [score=0.812 recalls=0 avg=0.620 source=memory/2026-08-27-run6.md:18-21]
<!-- openclaw-memory-promotion:memory:memory/2026-08-27-run6.md:24:24 -->
- Do not touch: hub code, ufw, zram, Parallel, Context7, GitHub MCP, hub agent without tools, Mini App. [score=0.812 recalls=0 avg=0.620 source=memory/2026-08-27-run6.md:24-24]
<!-- openclaw-memory-promotion:memory:memory/2026-08-27-run6.md:27:27 -->
- Secrets: Morning `memory/2026-08-27.md` contained an iCloud app-specific password in plaintext. Revoke it at appleid.apple.com. Do not copy the password into this file. [score=0.812 recalls=0 avg=0.620 source=memory/2026-08-27-run6.md:27-27]
<!-- openclaw-memory-promotion:memory:memory/2026-08-27.md:4:7 -->
- 🚀 R2D2 Hub развёрнут на hub.gbkz.uk (06:36–06:40): Дмитрий добавил A-запись `hub` → 138.124.180.178 в Cloudflare (сначала с опечаткой `hub.gbzk.uk` — имя вводил полным, Cloudflare сделал `hub.gbzk.uk.gbkz.uk`; исправил после разбора скриншота: в Name просто `hub`).; DNS: hub.gbkz.uk → Cloudflare proxy (172.67.223.229, 104.21.32.152), запись proxied (оранжевое облако).; nginx: включён `sites-enabled/hub.gbkz.uk` (прокси на 127.0.0.1:8091), конфиг валиден.; ⚠️ Vite preview блокировал хост: 403 «Blocked request.... [score=0.812 recalls=0 avg=0.620 source=memory/2026-08-27.md:4-7]
<!-- openclaw-memory-promotion:memory:memory/2026-08-27.md:8:11 -->
- 🚀 R2D2 Hub развёрнут на hub.gbkz.uk (06:36–06:40): ⚠️ certbot был сломан: pyOpenSSL 23.2 + cryptography 50 → `lib.GEN_EMAIL`; починил: `pip3 install --upgrade --break-system-packages pyopenssl` (26.4.0), затем josepy 1.14 несовместим (`X509Req`) → `pip3 install --upgrade --ignore-installed --break-system-packages josepy acme certbot certbot-nginx` (certbot 5.7.0). nginx не в PATH → запуск `PATH=/usr/sbin:$PATH certbot --nginx -d hub.gbkz.uk --redirect`.; ✅ Итог: HTTPS 200 (tls ok), http→https 301, сертификат Let's Encrypt до **25.11.2026**, автообновление настроено.... [score=0.812 recalls=0 avg=0.620 source=memory/2026-08-27.md:8-11]
<!-- openclaw-memory-promotion:memory:memory/2026-08-27.md:14:14 -->
- 📰 Дайджест (06:11, кнопка): Отправлен: Медуза (Цурило 79 лет, Рэтклифф в Москве, бензин), BAZA (криоконсервация), Коммерсантъ (лжеврачи, Непал, вирусная терапия, Кусама, 267 БПЛА). Курс ЦБ: USD 84.28 / EUR 98.29 / CNY 12.53. 14 постов, message_id=10590. RSS РБК отдал ошибку парсинга (no element found) — источник пропущен. [score=0.812 recalls=0 avg=0.620 source=memory/2026-08-27.md:14-14]
<!-- openclaw-memory-promotion:memory:memory/2026-08-27.md:17:20 -->
- 10:17–11:06 — AI Personal Hub (R2D2) развёрнут окончательно (ТЗ по OPENCLAW.md): Репо atlas-green-pearl-dawn смержен до c92757b («Document bot split, mini-PC deploy, hub watchdog»). npm ci + build, vite preview :8091 за nginx HTTPS → **https://hub.gbkz.uk** (200, title «AI Personal Hub»).; systemd-юнит `r2d2-hub.service` (EnvironmentFile .env, WorkingDirectory /root/atlas-green-pearl-dawn), watchdog cron раз в минуту через `scripts/hub-watchdog-cron.sh` (wrapper читает .env, не светит секреты в crontab), health :8091, автоперезапуск.; **Боты разделены** (по OPENCLAW.md): хаб-пейджер = **@HubAlertsbot** (id 8915951913, токен в .env... [score=0.812 recalls=0 avg=0.620 source=memory/2026-08-27.md:17-20]

## Promoted From Short-Term Memory (2026-09-03)

<!-- openclaw-memory-promotion:memory:memory/2026-08-27.md:21:24 -->
- 10:17–11:06 — AI Personal Hub (R2D2) развёрнут окончательно (ТЗ по OPENCLAW.md): **Admin-логика изменилась** (в новых коммитах): TELEGRAM_OWNER_ID больше НЕ даёт admin; admin = первый посетитель пустого хаба (`asAdmin = first`). Я очистил БД PGLite (/var/lib/r2d2/pglite) полностью → Дмитрий станет admin, открыв https://hub.gbkz.uk первым (имя → PIN → Настройки → AI-доступ → Проверить агента).; Чат хаба: OPENCLAW_GATEWAY_URL=http://127.0.0.1:18789 (без /v1), OPENCLAW_MODEL=openclaw/default, gateway.http.endpoints.chatCompletions.enabled=true — проверено: chat/completions 200, ответ «Работаю.».... [score=0.825 recalls=0 avg=0.620 source=memory/2026-08-27.md:21-24]
<!-- openclaw-memory-promotion:memory:memory/2026-08-27.md:27:30 -->
- 11:28–11:32 — Шаг 3 (финал): агент hub в OpenClaw: В openclaw.json `agents.list` = [{"id":"hub", tools.allow:[], skills:[]}], defaults.workspace=/root/openclaw. Gateway перезапущен, подхватил агента hub: текущая Telegram-сессия работает как `agent=hub` ✅; .env хаба (/root/atlas-green-pearl-dawn/.env) обновлён 11:27 (OPENCLAW_AGENT_ID, GATEWAY_TOKEN/URL, MODEL, PGLITE, TELEGRAM_*).... [score=0.825 recalls=0 avg=0.620 source=memory/2026-08-27.md:27-30]
<!-- openclaw-memory-promotion:memory:memory/2026-08-27.md:33:36 -->
- 11:38–12:00 — Хардненинг (ТЗ Дмитрия: безопасность+безотказность, без Docker/новых сервисов): **ufw**: уже был ок — снаружи только 22/80/443 + tailnet (100.64.0.0/10), default deny. 8091/8080/18789/8765 с WAN закрыты (8091 слушает 0.0.0.0, но ufw режет; loopback/tailnet достаточно).; **r2d2-hub**: переведён из user-юнита в СИСТЕМНЫЙ (/etc/systemd/system/r2d2-hub.service): Restart=on-failure, RestartSec=5, StartLimitBurst=5, StartLimitIntervalSec=120 (не always — битый билд не уйдёт в цикл).... [score=0.825 recalls=0 avg=0.620 source=memory/2026-08-27.md:33-36]

## Секреты: env-substitution (18.09)
- 8 credential-путей в `~/.openclaw/openclaw.json` переведены с плейнтекста на `${VAR}`: `gateway.auth.token`, `models.providers.{deepseek,openrouter,jina,openai,relaymodels}.apiKey`, `channels.telegram.botToken`, `mcp.servers.github.env.GITHUB_PERSONAL_ACCESS_TOKEN`. `relaymodels` был в таком виде уже раньше — это и есть рабочий паттерн хоста. <!-- project: github.com/Dmgromov01/openclaw-workspace -->
- Значения — `/root/.openclaw/secrets.env` (600), подключается systemd drop-in `20-secrets-env.conf` (`EnvironmentFile=-`, как `relaymodels.env`), НЕ система `config set --ref-provider`. Бэкап: `~/.openclaw/openclaw.json.pre-secretref.*`. Проверено: systemd отдаёт все 8 переменных дочернему процессу, `openclaw config validate` чист с загруженным env. <!-- project: github.com/Dmgromov01/openclaw-workspace -->
- Не применять ref-билдер (`--ref-provider default --ref-source env`) для этих путей: `--dry-run` показывает, что он резолвит ref против окружения CLI, и заодно ломает уже рабочий `${RELAYMODELS_API_KEY}`. <!-- project: github.com/Dmgromov01/openclaw-workspace -->
- Активация требует рестарта gateway (SSH, правило AGENTS.md). <!-- project: github.com/Dmgromov01/openclaw-workspace -->

## Инструменты: ключевые факты (14.09)

### Composio
- CLI-мост к внешним API (Gmail, GitHub и др.) через managed auth/OAuth
- Preflight обязателен перед первой операцией в каждом execution environment: `command -v composio` → `/root/.local/bin/composio`, `composio --version` ≥0.4.0, `composio whoami`. Install/upgrade/sign-in — только с approval оператора; authorization URL — только в private
- Путь: `/root/.composio/cli/composio`; версия ≥0.4.0 обязательна (текущая 0.4.1)
- 2026-09-17: путь `/root/.composio/cli/composio` добавлен в exec allowlist агента main (`openclaw approvals allowlist add --agent main`, откат — `allowlist remove`). Preflight пройден: `--version` → 0.4.1, `whoami` → dmgromov03@gmail.com / org dmgromov03_workspace. <!-- project: github.com/Dmgromov01/openclaw-workspace -->
- Auth: `composio whoami` → dmgromov03@gmail.com; активные: gmail, github, consensus_mcp
- Telegram НЕ подключен; для link нужен approval владельца
- Вызов: `composio execute <SLUG> -d '{...}'` — schema-first, connection-auto-check
- Не повторять uncertain write через другой интерфейс; authorization URL только в private
- Для внешних приложений предпочитать Composio skill + CLI, даже если пользователь не называет Composio

### Exec
- Allowlist-gated shell через gateway; headless = deny вне allowlist
- Allowlist: ls cat head tail df journalctl date uname free zramctl mkdir mv tar gpg git ss curl openclaw python3 grep find sqlite3 node npm
- Блокеры: systemctl не в списке; pipes/redirects/chains (`||`, `&&`, `|`) режутся
- Урок 14.09: прямая запись в exec_approvals_config SQLite ломает exec → только через safe-sqlite-edit.py

### safe-sqlite-edit.py
- Безопасная правка SQLite: автобэкап + JSON-валидация + ROLLBACK + лог
- Путь: `/root/openclaw/bin/safe-sqlite-edit.py`
- Все правки боевых БД только через этот скрипт

### Memory Search / Get
- Обязательный recall перед ответами о прошлом (SOUL.md directive)
- `memory_search` → snippets; `memory_get` → точные строки по path#line
- Никогда не угадывать прошлое; не нашёл → сказать «не нашёл»

### Sessions History / Search
- Доступ к переписке когда память не содержит факт
- Visibility=agent (только свои сессии); compaction может удалить старые
- Ключевые факты из переписки должны попадать в MEMORY.md сразу

### Conversations Send / List
- Отправка текста через каналы по conversationRef
- Только текст; файлы/медиа не поддерживаются напрямую
- telegram:1916536646 = conv_0998d33fb312f9c1d3d1232d365bd452

## Hub /health: Oura + PubMed + AI (2026-09-16)
- Раздел /health хаба работает на живых данных Oura API v2 напрямую (не через Composio): HRV/RHR/длительность сна/дыхание — из `sleep`, SpO2 — из `daily_spo2`, score — из `daily_sleep`/`daily_readiness`. Oura отдаёт максимум ~30–40 дней на запрос → чанкинг по 27 дней, дедуп по id. <!-- project: github.com/Dmgromov01/openclaw-workspace -->
- Evidence: Composio CLI `CONSENSUS_MCP_SEARCH` (toolkit `consensus_mcp`), парсинг текстового ответа в HealthEvidence, кэш 6 ч; AI-синтез — через штатный `chatViaUser` хаба. <!-- project: github.com/Dmgromov01/openclaw-workspace -->
- Hub `.env`: `OPENCLAW_MODEL` обязан быть `openclaw/default` (значение `openclaw/hub` ломает — агента `hub` нет), `OPENCLAW_AGENT_ID=chat`, а `OPENCLAW_GATEWAY_TOKEN` должен совпадать с `gateway.auth.token` (иначе 401). Проверенные связки gateway: `openclaw/default`+agent chat и `openclaw/chat`+agent chat → 200; `openclaw/main`+agent main → 500. <!-- project: github.com/Dmgromov01/openclaw-workspace -->

## Hub /health: почему AI-разбор падал (2026-09-16)
- Гейт доступа хаба: `chatViaUser` требует ОБА условия — `ai_mode='shared'` И `allow_global_ai=true`. У админа было `allow_global_ai=true`, но `ai_mode='off'` → «AI недоступен». Включено в PGLite `/var/lib/r2d2/pglite`, таблица `hub_users`. <!-- project: github.com/Dmgromov01/openclaw-workspace -->
- 500 `AgentSelectionRequiredError: ... session agent resolution has no explicit owner` = заголовок `x-openclaw-session-key` в шлюз отправлен НЕ agent-scoped. Голый `hub:<userId>` ломает выбор агента (агентов несколько). Правильно: `agent:<agentId>:hub:<userId>`. Пофикшено в `src/lib/server/openclaw.server.ts` (completeOpenAi). <!-- project: github.com/Dmgromov01/openclaw-workspace -->
- `AiAccessCard` (`src/components/settings/ai-access.tsx`) в хабе никуда не подключён — раздел «Настройки → AI-доступ» в UI отсутствует (мёртвый код). <!-- project: github.com/Dmgromov01/openclaw-workspace -->
