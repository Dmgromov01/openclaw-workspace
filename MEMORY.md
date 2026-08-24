# MEMORY.md — Долгосрочная память

_Курируемые воспоминания, свёрнутые из дневников `memory/YYYY-MM-DD.md`. Обновляется периодически._

## Домен (куплен 12.08.2026)
- **dmkz.org** — куплен Дмитрием. VPS IP для привязки: **138.124.180.178** (Франкфурт). DNS пока НЕ настроен (dmkz.org не резолвится), nginx не установлен, в openclaw.json домен не прописан. Деплой-план v3 заморожен до него; теперь можно размораживать по правилу релиза (тест → отчёт → «можно» → прод).

## Домен (деплой 12.08.2026, ПЕРЕДЕПЛОЙ 19.08.2026 на новый сервер)
- **gbkz.uk** — ОСНОВНОЙ домен, куплен напрямую на Cloudflare (не РФ-регистратор, NS alina/damien.ns.cloudflare.com). Цепочка: Cloudflare (DNS+прокси, A → 138.124.180.178) → nginx (TLS Let's Encrypt, сайт /etc/nginx/sites-available/gbkz.uk, слушает 80+443, прокси на 127.0.0.1:18789) → OpenClaw. Работает: HTTPS 200, редирект http→https, www → 200, WSS-хендшейк 200, сертификат до **17.11.2026** (автообновление certbot.timer).
- Креды Cloudflare (R2 API): `/root/.openclaw/credentials/cloudflare/r2.json` (chmod 600, ВНЕ git). Account id a068ea..., endpoint *.r2.cloudflarestorage.com. Дмитрий сам обновил A-запись 19.08.
- **dmkz.org** — заброшен у Timeweb (РФ-регистратор, addPeriod-блок смены NS), НЕ используется.
- Конфиг OpenClaw: `gateway.remote.url` = wss://gbkz.uk; `gateway.controlUi.allowedOrigins` включает gbkz.uk (+ www + Tailscale как fallback для iPhone); `gateway.auth.mode` = **token** со статическим токеном (сменён с password — iPhone шлёт device-token).
- ⚠️ **УРОК (12.08)**: iPhone подключается к гейтвею через **код настройки (setup code)** — генерировать `openclaw qr --url wss://gbkz.uk --setup-code-only` (или просто `openclaw qr`). Это САМЫЙ простой и надёжный путь, не пароль/токен/порт. Поле «код настройки» на iPhone.
- ⚠️ **Урок (12.08)**: порт для iPhone — **443** (через nginx), НЕ 18789 (18789 открыт только локально). НЕ переключать auth.mode в password обратно.
- ✅ **Интеграционное тестирование закрыто 12.08**: HTTPS 200, SSL до 10.11.2026, WSS-хендшейк работает, авторизованный WSS (token) → connect → hello-ok ✅, прямой DeepSeek API генерирует ответ ✅. Нюанс: `talk`-метод по WSS требует scope operator.admin (статический токен не даёт) — ограничение протокола, не неисправность; для чата DeepSeek работает через агента напрямую.
- 🧪 Плагин `model-router` (гибрид DeepSeek-direct + OpenRouter Vision) — заморожен, в `plugins.entries` НЕ включён (SDK не имеет LLM-хука). Гибрид работает нативно через провайдеры в openclaw.json (deepseek + openrouter оба с ключами). Провайдер в конфиге называется `deepseek` (не deepseek-direct).

## Кто мой человек
- **Дмитрий** (@Dm_GRM), русскоязычный. Основной сервер OpenClaw — **VPS vps-7182** (IP **138.124.180.178**, Франкфурт DE, Ubuntu 24.04, 2 vCPU / 2 GB RAM / 20 GB SSD, хост Tailscale **hiplet-109548** = **100.113.115.17**, тайлнет tail6a4baa). `vps-amnezia` (100.79.152.33) — другой узел Tailscale, НЕ мой рабочий. Модель: `deepseek/deepseek-chat` (= DeepSeek V4 Flash через прямой API). Забыты старые серверы — не путать.
- iPhone сопряжён (auth-токен, Tailscale `hiplet-109548.tail6a4baa.ts.net:443`).
- Telegram-владелец: id **1916536646**, бот **@Dmbotmy_bot** (токен в конфиге). Раньше был @Dm_GRM — основной TG-аккаунт.

## 🔒 КОНСТАНТА (#1178): В боте — ТОЛЬКО РЕЗУЛЬТАТ
- В Telegram-чат отправлять ТОЛЬКО готовый результат. Никаких размышлений, «сейчас сделаю», логов, пояснений — в чат только чистый итог. Применять ко ВСЕМ командам навсегда. (Записано и в AGENTS.md.)

## 🧠 Принцип Дмитрия (#1145, ОБНОВЛЁН 15.08): мыслить как фулстек-архитектор
- Внутренние размышления — на уровне фулстек-архитектора: видеть всю систему целиком, слои, зависимости, узкие места.
- Ответы в чат — максимально лаконичные, короткие, по факту. Без воды и разжёвывания.
- ⚠️ **ОБЯЗАТЕЛЬНО (15.08)**: ВСЕ изменения памяти/файлов/настроек коммитить и пушить в репозиторий (`git add . && git commit && git push`). Ничего не оставлять только локально.
- (Ранее: «решать проще, без ухода в IT» — заменено этим принципом.)

## Инфраструктура / критичные настройки
- **Компакция** (`agents.defaults.compaction`): актуально на 24.08 — `maxActiveTranscriptBytes: "2mb"`, `truncateAfterCompaction: true`, `reserveTokensFloor: 100000`, `reserveTokens: 450000`, `keepRecentTokens: 200000`, `midTurnPrecheck.enabled: true`, mode safeguard. Бэкапы: openclaw.json.bak-pre-* (см. /root/.openclaw).
  ⚠️ **Урок (11.08, повторно падало)**: диалог раздулся до ~114K токенов, а лимит был `keepRecentTokens: 100000` → перебор на 14K, сжатие падало с `already_compacted_recently` → «context overflow / auto-compaction could not recover». Диагностика по логам: `[context-overflow-precheck] estimatedPromptTokens > promptBudgetBeforeReserve` + `[compaction-diag] outcome=failed reason=already_compacted_recently`.
  **Правило**: `keepRecentTokens` держать ЗАВЫШЕННЫМ относительно пикового размера диалога (у DeepSeek 1M ctx — запас есть), иначе карусель overflow → already_compacted → фейл. `reserveTokensFloor` (подсказка про 35000) тут НЕ решает — он и так был 100000. Поля protected — править напрямую в `openclaw.json` + restart (`config.patch` блокирует).
- **Модели**: primary `deepseek/deepseek-v4-flash` (прямой API, дёшево 1M ctx). Провайдеры в конфиге (19.08, ключи восстановлены): **deepseek** · **openrouter** (auto, qwen/qwen-image-3-pro, + openai/text-embedding-3-small с 24.08) · **google** (gemini-3.1-flash-image-preview, gemini-2.5-flash) — все с apiKey. **DeepSeek НЕ принимает картинки** — для image использовать Gemini/OpenRouter. Ключи: `/root/.openclaw/credentials/` (openrouter.key, ai-studio.key, github.token, telegram-app.json, jina.key — все chmod 600, ВНЕ git). ⚠️ Схема моделей провайдера не принимает `output`/`input:["text","image"]` — только `input:["text"]` (+api/contextWindow/maxTokens). ⚠️ **Урок 24.08**: memorySearch требует, чтобы embedding-модель была в каталоге провайдера, иначе векторная часть гибрида молча не работает. OpenRouter не показывает embedding-модели в GET /models, но POST /v1/embeddings работает.
- **Файрвол (ufw)**: **ACTIVE с 24.08** (после аудита был INACTIVE!): 22/80/443 open + tailnet (100.64.0.0/10), default deny incoming / allow outgoing. Порт 8080 (miniapp) — ТОЛЬКО 127.0.0.1 (переведён 24.08), наружу закрыт.
- **Swap 2GB** на новом сервере — создан.

## Календарь — GOOGLE API (переехали с iCloud; iCloud УСТАРЕЛ)
- ⚠️ **Актуальный календарь — Google Calendar** (`dmgromov03@gmail.com`), НЕ iCloud.
- Скрипт: `calendar/gcal_reader.py` (service-account `/root/.openclaw/credentials/gcal/service-account.json`). Команды: `today`, `week`, `list --days N`. Даты Europe/Moscow.
- **Google API только ЧИТАЕТ** (нет add/delete в gcal_reader). Добавление событий — НЕ реализовано на Google. `icloud_calendar.py` и `orchestrator.py` — 🗑️ **УДАЛЕНЫ 24.08** (в `_trash_/batch3-20260824`), нестыковка с `import icloud_calendar` исчезла.
- Проверено 11.08: `gcal_reader.py today` вернул реальное событие («Тест: подключение календаря OpenClaw» 13:00) — Google API работает.
- 07.08 чистили мусор ещё в iCloud. Пометка «позвонить Петрову 18.08.2026» — из старого iCloud-демо, к Google не относится.

## Телеgram-интерфейс (кнопки) — используется для расписания Google Calendar
- **Вариант Б (reply-клавиатура)** — работает: кнопки «📅 Расписание на день», «📅 Расписание на неделю», «📰 Дайджест» над полем ввода. Нажатие = обычное сообщение с текстом кнопки. Кнопка «Очистить месяц» НЕ нужна.
- ⚠️ **КНОПКА «📰 Дайджест» (= команда «дайджест») = ТОЛЬКО персональный дайджест** (`calendar/digest.py`): RSS (РБК, Коммерсантъ) + TG-каналы (Медуза, Важные истории, The Bell, BAZA) + курс ЦБ, отправка владельцу через бота. НЕ расписание, НЕ web_search, НЕ Google News.
- 🔒 **КОНСТАНТА ФОРМАТА ДАЙДЖЕСТА (15.08, требование Дмитрия)**:
  - Блоки СТРОГО ПО ИСТОЧНИКАМ (Медуза/Важные истории/The Bell/BAZA/РБК/Коммерсантъ), НЕ по тематике, НЕ перемешивать.
  - Внутри каждого источника — краткое связное ИИ-саммари от DeepSeek (по каждому источнику отдельно), подробно, с сохранением контекста/цифр, без искажений и выдумывания.
  - Обрезка текста — ТОЛЬКО по целому слову с многоточием (`_clip`), никогда не рвать на полуслове.
  - В конце — курс ЦБ (USD/EUR/CNY) + счётчик постов.
  - ⚠️ Авторизация DeepSeek в digest.py: `Authorization: "Bearer " + ключ` (заглушка `"***"` даёт 401). Ключ — из `/etc/openclaw/secrets.json` по `deepseek_key` (id `/deepseek_key`).
- ⚠️ Кнопки «расписание» должны теперь дёргать **Google Calendar** (`gcal_reader.py`), НЕ `icloud_calendar.py` (устарел). Проверить/переключить при следующей доработке.
- 🔧 **Как работает дайджест (tech)**: скрипт `calendar/digest.py`; запуск `python3 digest.py` (собирает и ОТПРАВЛЯЕТ владельцу через бота), `--no-send` — только вывод, `--hours N` — окно (по умолчанию WINDOW_HOURS=2). Источники: TG-каналы через t.me/s (meduzalive, istories_media, thebell_io, bazabazon — SOCKS НЕ нужен) + RSS (РБК, Коммерсантъ) + курс ЦБ (cbr-xml-daily). Отправка — `calendar/bot_sender.py` (sendMessage на chat 1916536646, parse_mode=HTML; при HTTP 400 — fallback без parse_mode, фикс 19.08). AI-саммари (DeepSeek): ключ теперь берётся из `openclaw.json → models.providers.deepseek.apiKey` (добавлен 19.08 из auth store sqlite; раньше — `/etc/openclaw/secrets.json` по `deepseek_key`, на новом сервере файла НЕТ).
- Нативные команды `/den` итд — отменены (имя только латиница; `customCommands` — отдельное поле верхнего уровня `channels.telegram.customCommands`).
- По кнопкам — ТОЛЬКО чистый список `• ДД.ММ.ГГГГ ЧЧ:ММ — summary` без заголовков (константа выше).

## Личный Telegram-аккаунт (MTProto / Telethon)
- Сервис `/root/telegram-user-svc/server.py` (HTTP `127.0.0.1:8765`) — **systemd unit** `telegram-user-svc.service` (важно: systemd перезапускает, pkill бесполезен). Endpoint'ы: /auth/status, /auth/start, /auth/code, /auth/password, /send, /send_file, /dialogs, /history.
- 🔄 **ПЕРЕСОЗДАН на новом сервере 19.08** (по команде Дмитрия): venv + telethon 1.44 + aiohttp 3.14, config.json из telegram-app.json (api_id 33037521, api_hash, password пустой), сервис active на порту 8765. ✅ **Авторизация ПРОЙДЕНА 20.08** (`authorized: true`, self=Дмитрий 1916536646).
- Плагин `~/.openclaw/plugins/tg-user-tools/` → инструменты **tg_send, tg_send_file, tg_dialogs, tg_history** (создан заново, подключён в plugins.load.paths + entries; ⚠️ загрузку проверить).
- **Формат плагина**: `definePluginEntry` из `openclaw/plugin-sdk/plugin-entry` + `api.registerTool({name,description,parameters,execute})`; объявить `contracts.tools` в `openclaw.plugin.json` И `package.json` (`openclaw.contracts.tools`). Manifest требует `configSchema` (пустой объект).
- Скрипт отправки фото: `/root/telegram_user_send_photo.sh <target> <path> [caption]`.
- Саммари диалогов: Вариант 2 (свободный текст через агента) — работает, кнопочный флоу не нужен.

## Картинки (мем-автоматизация УБРАНА 11.08 по решению Дмитрия)
- Мем-рассылка отменена полностью: `meme_fetcher.py` удалён, cron-задач нет.
- **Pollinations** — бесплатная генерация картинок без ключа: `calendar/image_gen.py` (`https://image.pollinations.ai/prompt/<p>?width=&height=&nologo=true&model=flux`). Не встроенный провайдер OpenClaw — только через скрипт.
- 🔒 **ПРАВИЛО (19.08, согласовано с Дмитрием):** генерации С НУЛЯ (без референса — ракетка, лого, обои, «нарисуй...») → ВСЕГДА бесплатный Pollinations (`python3 calendar/image_gen.py "<промпт>" [w] [h]`), НЕ `image_generate` (дорого ~$1/день через OpenRouter→Gemini). `image_generate` — ТОЛЬКО для редактирования по присланному фото (пёс-леопард, портреты, визитки) и когда нужно высокое качество/точность.
- **Gemini-ретушь** подключена (gemini-3.1-flash-image-preview, baseUrl обязателен) — НО упёрлась в квоту 429 (подписка Pro ≠ квота API-ключа). Открытые API ретуши (GFPGAN/Real-ESRGAN на HF) — нестабильны, не гонять.

## WhatsApp — ЗАКРЫТ (не возвращаться без явного запроса)
- Baileys блокируется с дата-центр IP («Не удалось связать устройство»). WhatsApp Business API — не настраивали. Пользователь: «забываем про вотсап». Xray/VPN оставлен.

## Xray/VPN
- Xray-core v26.3.27, VLESS-подписка `https://xo.e0f.cx/sub/tppNyEo0H9V6KByn` (нужен UA v2rayNG/1.8.5). Все серверы — дата-центры (для /apps/create бесполезны). Выгодные узлы: Германия. Локальный SOCKS5/HTTP на 127.0.0.1:10808/10809; сейчас порт WARP 4001 — для браузера через прокси.
- my.telegram.org доступен с сервера; создание приложения блокируется для дата-центр IP → помог **Cloudflare WARP** (WarpProxy 127.0.0.1:4001, не помечается как хостинг). **TG_API_ID/HASH уже получены** (см. хвосты).

## Прошлые ошибки (не повторять)
- `pkill -f "python3 server.py"` убивает сам процесс выполнения — использовать точный путь/pgrep.
- Не добавлять модель в primary до добавления в каталог (иначе `agents.defaults.model failed`).
- Поиск image-моделей OpenRouter по `/models` — битый (image-генераторы не в списке; вызываются через `/api/v1/images`). Кеш `/tmp/or_models.json` недостоверен — проверять по живой странице.
- DeepSeek id-алиасы: `deepseek-chat` и `deepseek-reasoner` оба → v4-flash.
- Не тонуть в IT там, где есть простой путь (урок Дмитрия).

## GitHub (сделано 11.08)
- Приватный репо: **https://github.com/Dmgromov01/openclaw-workspace** (private), ветка main, первый коммит `2e2e689`. Секреты вычищены до пуша (2FA/phone/code/sk-or → плейсхолдеры), .gitignore исключает .env/.session/tg-mtproto/media/_trash_/state-json/node_modules. Токен почищен из env/remote.

## 🔴 АКТИВНЫЕ ХВОСТЫ (по приоритету)
1. ~~**Личный TG: вход в telegram-user-svc**~~ — ✅ ЗАКРЫТ 20.08: авторизован (`authorized: true`, self=Дмитрий 1916536646).
2. **Дайджест @de574574 (Екатерина)** — TG авторизован 20.08, теперь доступен. (Реализовать отправку при необходимости.)
3. **Image-gen через `image_generate` tool** — ретушь Gemini ждёт квоты (429). Открытые HF-сервисы нестабильны. (qwen-image — закрыто решением Дмитрия, убрано.)
4. ~~`_collect_news` в orchestrator.py~~ — 🗑️ УДАЛЁН 24.08 вместе с orchestrator.py (мёртвый код).
5. ⚠️ **R2D2 (19.08): billing error — у какого-то ключа кончились кредиты** — проверить балансы OpenRouter/Google/DeepSeek.
6. ~~meme_fetcher.py~~ — УДАЛЁН (мем-автоматизация убрана 11.08).
7. MiMo v2.5 и Hy3 :free — добавлять ли в каталог OpenRouter (Дмитрий рассматривал, не подтвердил). Vision-чтение после удаления gpt-4o-mini — чем читать скрины.
8. ✅ Плагин tg-user-tools загружен (лог: `2 plugins: telegram, tg-user-tools`), инструменты tg_send/tg_send_file работают (отправка .ics 20.08).
9. ✅ **Плагин jina-tools (jina_search, jina_rag) — подключён 24.08** (entries+load+allow, лог: 7 plugins). Ключ: `/root/.openclaw/credentials/jina.key`. Кэш RAG: `/root/.openclaw/cache/jina_rag.json` (10MB). Rate limit Jina: 100K токенов/мин — троттлинг встроен.
10. 🔒 **Bot token @Dmbotmy_bot РОТИРОВАН 24.08 12:09** (утёк в git-историю; старый мёртв 401, новый в openclaw.json+.env, НЕ писать в git/логи).

## Расписание/календарь (последнее известное, Google)
- По Google Calendar на 11.08: событие «Тест: подключение календаря OpenClaw» 13:00 (проверка подключения).
- Старое «Встреча с Катей по кольцам оура 18:30» (07.08) — было в iCloud, актуальность проверять вживую через gcal_reader.

## 🔒 ПРАВИЛО РЕЛИЗА (15.08.11, требование Дмитрия)
- НИЧЕГО в прод без явного «можно» от Дмитрия. Процесс: тест в ~/.openclaw-test (порт 18790, без TG-бота) → отчёт (что/что проверил/риски) → вопрос → только после «можно» катить в прод.
- ⚠️ **Урок 24.08**: тестовый контур `--profile test` на текущем сервере НЕ поднимается, пока активен прод (guard блокирует второй гейтвей). Скрипт `/root/.openclaw/deploy-test-to-prod.sh` на новом сервере ОТСУТСТВУЕТ. Альтернатива: правка конфига файлом + `systemctl --user restart openclaw-gateway.service` (с явного «можно»).
- image_generate настроен: primary openrouter/google/gemini-3.1-flash-image, fallback google + openrouter gemini-3-pro (поля protected — править напрямую в openclaw.json + restart).
- Я нарушил это правило (serve в прод) 15.08.11 — Дмитрий отчитал. Больше не повторять.

## Module: Excel Tools & Function Calling
- **File**: `skills/excel_skills.py`
- **Class**: `ExcelSkillsHandler`
- **Supported Tools**:
  - `excel_sql_query`: выполнение SQL-запросов DuckDB напрямую по Excel файлам.
  - `excel_table_search`: поиск по строкам с извлечением метаданных (лист, строка).
  - `excel_generate_report`: построение форматированных управленческих отчётов с графиками и формулами.
- **Dependencies**: `openpyxl`, `pandas`, `duckdb`, `tabulate`.

## Module: Telegram File Handler & Reporting
- **File**: `bot/file_handler.py`
- **Directories**:
  - `storage/uploads/`: временное хранение загруженных пользователем `.xlsx`, `.csv`, `.pdf`.
  - `storage/reports/`: сгенерированные `.xlsx` отчеты и визуализации.
- **Capabilities**:
  - Прием и автоматический аудит структуры таблиц при загрузке.
  - Двусторонняя доставка сгенерированных отчетов и диаграмм напрямую в чат.

## Module: Telegram Mini App Final Spec
- **Target Device**: iPhone 17 Pro Max (Large typography, light theme).
- **Core Widgets**:
  1. Weather Widget (Real-time).
  2. Calendar & Quick Tasks (Google Calendar / Tasks integration).
  3. Channels & RSS Hub with full AI-Digest reader.
  4. CBR Multi-Currency Converter (USD, EUR, CNY, JPY, GBP, RUB).
  5. Password Generator (12-32 chars).

## Module: Mini App Telegram Bot Connector
- **File**: `bot/miniapp_menu.py`
- **Features**:
  - Установка MenuButtonWebApp в строку ввода Telegram.
  - Инлайн-клавиатура с WebAppInfo для быстрого доступа к Personal Hub.
  - Интеграция переменной окружения `MINIAPP_URL`.

## Module: Telegram Mini App v3
- **Tasks & Archive**:
  - Direct checkbox toggle into archive with animated strike-through.
  - Separate archive view with task restore and full wipe options.
  - Persistent storage in `localStorage`.
- **Precipitation Radar**:
  - Integrated RainViewer radar tile layers + Leaflet.js.
  - Hourly time scrubber (-2h to +30m).
- **Sources Management**:
  - Live list of connected TG channels & RSS feeds with 1-click delete.
