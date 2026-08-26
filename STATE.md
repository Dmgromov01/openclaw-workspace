# STATE.md — Актуальное состояние (НАПОМИНАЛКА)

> **Читай этот файл первым при старте/перед работой с календарём и интеграциями.**
> Здесь зафиксировано ЧТО СЕЙЧАС реально работает. Обновляй при каждом изменении, чтобы не было нестыковок.

## 📅 Календарь — СЕЙЧАС = GOOGLE CALENDAR API (НЕ iCloud!)
- ⚠️⚠️ **Мы перешли с iCloud на Google Calendar API. ВСЕ новые работы с календарём — через Google.**
- Аккаунт: `dmgromov03@gmail.com`, service-account: `/root/.openclaw/credentials/gcal/service-account.json`
- Скрипт: `calendar/gcal_reader.py` — **ЧТЕНИЕ** (today / week / list --days N), даты Europe/Moscow.
- Проверено 11.08: `python3 calendar/gcal_reader.py today` → вернул «Тест: подключение календаря OpenClaw 13:00» ✅ работает.
- **ДОБАВЛЕНИЕ/УДАЛЕНИЕ событий на Google пока НЕ реализовано** (gcal_reader только читает). Если понадобится add/delete — написать в gcal_reader.py (svc.events().insert/delete).
- `icloud_calendar.py` — 🗑️ **УДАЛЁН 24.08** (в `_trash_/batch3-20260824`), `orchestrator.py` тоже удалён (мёртвый код). Календарь = только Google.

## 🔔 Кнопки в Telegram (расписание) — должны дёргать GOOGLE
- Кнопки «📅 Расписание на день/неделю», «📰 Дайджест» (reply-клавиатура) есть, но их обработка сейчас ведёт на старое. При доработке — переключить на `gcal_reader.py`.
- По кнопкам — ТОЛЬКО чистый список `• ДД.ММ.ГГГГ ЧЧ:ММ — summary` без заголовков (константа Дмитрия).

## 🔌 Личный Telegram (MTProto) — РАБОТАЕТ (вход выполнен 20.08)
- `telegram-user-svc` (systemd `telegram-user-svc.service`, HTTP 127.0.0.1:8765) — **active**, авторизован (`authorized: true`, self = Дмитрий 1916536646).
- Инструменты агента: tg_send, tg_send_file, tg_dialogs, tg_history (плагин tg-user-tools).

## 🖼 Картинки
- Генерация по запросу: `calendar/image_gen.py` (Pollinations/Flux, бесплатно, без ключа).
- Мем-АВТОМАТИЗАЦИЯ УБРАНА 11.08 (meme_fetcher.py удалён, cron-задач нет).
- Gemini-ретушь: подключена, но упёрлась в квоту 429 — ждать.
- qwen-image-3-pro (OpenRouter): плагин есть, ключ не подхватывается — активный хвост.

## 🌐 Инфраструктура
- Сервер (основной, OpenClaw): VPS `vps-7182`/hiplet-109548, IP 138.124.180.178 (Франкфурт DE), Ubuntu 24.04, 2 vCPU/2GB/20GB, Tailscale hiplet-109548 = 100.113.115.17 (в тайлнете tail6a4baa). `vps-amnezia` (100.79.152.33) — отдельный узел, не рабочий.
- Сервер для личного VPN (AmneziaWG): старый 83.219.98.98 (оплачен до 10.11.2026). Старые серверы/IP забыты.
- **Файрвол ufw: ACTIVE с 24.08** (включён после аудита): 22/80/443 open + tailnet 100.64.0.0/10; default deny incoming. Порт 8080 (miniapp) — ТОЛЬКО loopback (127.0.0.1), наружу закрыт.
- Swap 2GB. Модель: deepseek/deepseek-v4-flash (V4 Flash, прямой API).
- GitHub: приватный репо Dmgromov01/openclaw-workspace (main).
- **Bot token @Dmbotmy_bot РОТИРОВАН 24.08 12:09** (утёк в git-историю; старый мёртв 401, новый в openclaw.json+.env, вне git).
- Плагины прод: deepseek, tg-user-tools, openrouter, google, perplexity, parallel, memory-core, **jina-tools** (24.08).

## 📱 Mini App (Personal Hub)
- Стек: **Python** (`miniapp/server.py` + `auth.py`), systemd `miniapp.service`, nginx `/miniapp/` → 127.0.0.1:8080 (loopback, наружу закрыт).
- **Фаза 1 безопасности (26.08)**: сессии в БД = **SHA-256 хеш** токена (не plaintext); пароли **PBKDF2 100k** (старый sha256-формат при логине автоматически переписывается в PBKDF2); владелец — из `TELEGRAM_OWNER_ID` (env, без хардкода); **AI через OpenClaw gateway** (`/v1/chat/completions`), не DeepSeek напрямую; **BYOK** AES-256-GCM (в UI только хвост ключа); админка: allowed / role / allow_global_ai / quota_daily / удаление / аудит; источники RSS — только https, не private IP, лимит 12.
- Env (в `.env`, вне git): `TELEGRAM_OWNER_ID`, `OPENCLAW_GATEWAY_URL`, `OPENCLAW_GATEWAY_TOKEN`, `AI_KEY_SECRET`, `TELEGRAM_BOT_TOKEN`.

## 🔴 Активные хвосты (кратко)
1. Дайджест @de574574 (Екатерина) — личный TG авторизован (20.08), реализовать отправку при необходимости.
2. Image-gen через `image_generate` tool — Gemini-ретушь ждёт квоты (429).
3. Добавление событий в Google Calendar не реализовано (gcal_reader только читает).
4. R2D2 (19.08): billing error — проверить балансы OpenRouter/Google/DeepSeek.
5. MiMo v2.5 / Hy3 :free в каталог OpenRouter — Дмитрий не подтвердил. Vision-чтение скринов после удаления gpt-4o-mini — чем читать.

> Если что-то перестало соответствовать реальности — **обнови этот файл** и MEMORY.md.
