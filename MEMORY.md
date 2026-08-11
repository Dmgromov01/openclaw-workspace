# MEMORY.md — Долгосрочная память

_Курируемые воспоминания, свёрнутые из дневников `memory/YYYY-MM-DD.md`. Обновляется периодически._

## Кто мой человек
- **Дмитрий** (@Dm_GRM), русскоязычный. Сервер OpenClaw сначала на Beget (5.181.108.40, STB), с ~14:00 2026-08-10 — новый VPS (vps-7182, `vps-amnezia`, Tailscale 100.79.153.33). Модель: `deepseek/deepseek-chat` (= DeepSeek V4 Flash через прямой API).
- iPhone сопряжён (auth-токен, Tailscale `zdgnusmnqx.tail6a4baa.ts.net:443`).
- Telegram-владелец: id **1916536646**, бот **@Dmbotmy_bot** (токен в конфиге). Раньше был @Dm_GRM — основной TG-аккаунт.

## 🔒 КОНСТАНТА (#1178): В боте — ТОЛЬКО РЕЗУЛЬТАТ
- В Telegram-чат отправлять ТОЛЬКО готовый результат. Никаких размышлений, «сейчас сделаю», логов, пояснений — в чат только чистый итог. Применять ко ВСЕМ командам навсегда. (Записано и в AGENTS.md.)

## 🧠 Принцип Дмитрия (#1145): решать ПРОЩЕ, без глубокого ухода в IT
- Сначала самое простое: обычный поиск/браузер/готовый каталог. Код/curl/автоматизация — только когда простой путь не работает, и в меру. (Дважды озвучен 07.08.)

## Инфраструктура / критичные настройки
- **Компакция** (`agents.defaults.compaction`): `maxActiveTranscriptBytes: "0"` (защита от сбоя автооптимизации), плюс reserveTokens 40000/50000, keepRecentTokens 100000, midTurnPrecheck.enabled true.
- **Модели**: primary `deepseek/deepseek-chat` (v4-flash, прямой API, дёшево 1M ctx). Провайдеры: deepseek · openrouter · google. **DeepSeek НЕ принимает картинки** — для image использовать GPT-4o/Gemini/qwen-image. Vision-чтение скринов: gpt-4o-mini был удалён из каталога (см. хвосты).
- **Файрвол (ufw)**: SSH 22 открыт, tailnet (100.64.0.0/10) пропущен, порт device-pair 18789 — только из tailnet. Default deny incoming / allow outgoing.
- **Swap 2GB** на новом сервере — создан.

## Календарь (iCloud Home) — работает
- Скрипт: `calendar/icloud_calendar.py`. Календарь **Home** из `ICLOUD_CALENDAR_URL` в `/root/tg_bot/.env`.
- Операции: add «действие+дата+время», today/week/month, delete --search/--date. Даты Europe/Moscow.
- `cal.search` падал 412 на iCloud → переписано на `cal.events()` + локальная фильтрация.
- 07.08 почищены дубли/мусор в календаре. Демо «позвонить Петрову 18.08.2026» — уточнить, нужно ли удалить.

## Telegram-интерфейс (кнопки)
- **Вариант Б (reply-клавиатура)** — ИТОГОВЫЙ, работает: кнопки «📅 Расписание на день», «📅 Расписание на неделю», «📰 Дайджест» над полем ввода. Нажатие = обычное сообщение с текстом кнопки. Кнопка «Очистить месяц» НЕ нужна.
- Нативные команды `/den` итд — отменены (имя только латиница; `customCommands` — отдельное поле верхнего уровня `channels.telegram.customCommands`).
- Плагин `~/.openclaw/plugins/menu-buttons/` (registerInteractiveHandler) — для inline-кнопок; reply-клавиатуру шлём напрямую через Bot API.
- По кнопкам — ТОЛЬКО чистый список `• ДД.ММ.ГГГГ ЧЧ:ММ — summary` без заголовков (константа выше).

## Личный Telegram-аккаунт (MTProto / Telethon)
- Сервис `/root/telegram-user-svc/server.py` (HTTP `127.0.0.1:8765`) — **systemd unit** `telegram-user-svc.service` (важно: systemd перезапускает, pkill бесполезен). Endpoint'ы: /auth/status, /auth/start, /auth/code, /auth/password, /send, /dialogs, /history.
- Плагин `~/.openclaw/plugins/tg-user-tools/` → инструменты **tg_send, tg_dialogs, tg_history** (работают; `toolNames:[]` в inspect — это статическая метадата, не рантайм).
- **Формат плагина**: `definePluginEntry` из `openclaw/plugin-sdk/plugin-entry` + `api.registerTool({name,description,parameters,execute})`; объявить `contracts.tools` в `openclaw.plugin.json` И `package.json` (`openclaw.contracts.tools`).
- Саммари диалогов: Вариант 2 (свободный текст через агента) — работает, кнопочный флоу не нужен.

## Картинки (мем-автоматизация УБРАНА 11.08 по решению Дмитрия)
- Мем-рассылка отменена полностью: `meme_fetcher.py` удалён, cron-задач нет.
- **Pollinations** — бесплатная генерация картинок без ключа: `calendar/image_gen.py` (`https://image.pollinations.ai/prompt/<p>?width=&height=&nologo=true&model=flux`). Не встроенный провайдер OpenClaw — только через скрипт.
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
1. **Личный TG re-login / разбан** — flood-ban (FLOOD_WAIT ~80134s с 08:40 11.08) спадает ~06:56 UTC 12.08 (09:56 МСК). `telegram-user-svc` ОСТАНОВЛЕН (`systemctl stop/disable`) до успешного входа. **НЕ ретраить до бана.** План на ~07:30 UTC 12.08: один чистый code-login через NL-прокси, 2FA из конфига, затем `systemctl enable --now`, перезапуск server.py.
2. **Дайджест @de574574 (Екатерина)** — недоступен до авторизации личного TG. Сделать после релогина (1 день).
3. **🔴 Image-генерация qwen-image-3-pro** (OpenRouter `/api/v1/images`) — кастомный провайдер-плагин `openrouter-qwen-image` создан, но ключ не подхватывается из пер-агентного auth (ищется по id провайдера в sqlite). Тест `paste-api-key --provider openrouter-qwen-image` + проверка `auth-profiles.json` + повторный тест генерации.
4. **Image-gen через `image_generate` tool** — в qwen нет; ретушь Gemini ждёт квоты (429). Открытые HF-сервисы нестабильны.
5. `_collect_news` в orchestrator.py — всё ещё **заглушка** (дайджест собран вручную). Реализовать реальный сбор.
6. ~~meme_fetcher.py~~ — УДАЛЁН (мем-автоматизация убрана 11.08).
7. MiMo v2.5 и Hy3 :free — добавлять ли в каталог OpenRouter (Дмитрий рассматривал, не подтвердил). Vision-чтение после удаления gpt-4o-mini — чем читать скрины.
8. Проверить device-pair 18789 после закрытия файрвола на весь мир.

## Расписание/календарь (последнее известное)
- На 07.08 единственное событие: «Встреча с Катей по кольцам оура» 18:30. (Актуальность проверить вживую через icloud_calendar.)
