# STATE.md — Актуальное состояние (НАПОМИНАЛКА)

> **Читай этот файл первым при старте/перед работой с календарём и интеграциями.**
> Здесь зафиксировано ЧТО СЕЙЧАС реально работает. Обновляй при каждом изменении, чтобы не было нестыковок.

## 📅 Календарь — СЕЙЧАС = GOOGLE CALENDAR API (НЕ iCloud!)
- ⚠️⚠️ **Мы перешли с iCloud на Google Calendar API. ВСЕ новые работы с календарём — через Google.**
- Аккаунт: `dmgromov03@gmail.com`, service-account: `/root/.openclaw/credentials/gcal/service-account.json`
- Скрипт: `calendar/gcal_reader.py` — **ЧТЕНИЕ** (today / week / list --days N), даты Europe/Moscow.
- Проверено 11.08: `python3 calendar/gcal_reader.py today` → вернул «Тест: подключение календаря OpenClaw 13:00» ✅ работает.
- **ДОБАВЛЕНИЕ/УДАЛЕНИЕ событий на Google пока НЕ реализовано** (gcal_reader только читает). Если понадобится add/delete — написать в gcal_reader.py (svc.events().insert/delete).
- `icloud_calendar.py` — 🗑️ **УСТАРЕЛ** (legacy от старой системы iCloud). Не использовать как основной. В `orchestrator.py` остался `import icloud_calendar as cal` — ❗ нестыковка, при доработке перевести на gcal_reader.

## 🔔 Кнопки в Telegram (расписание) — должны дёргать GOOGLE
- Кнопки «📅 Расписание на день/неделю», «📰 Дайджест» (reply-клавиатура) есть, но их обработка сейчас ведёт на старое. При доработке — переключить на `gcal_reader.py`.
- По кнопкам — ТОЛЬКО чистый список `• ДД.ММ.ГГГГ ЧЧ:ММ — summary` без заголовков (константа Дмитрия).

## 🔌 Личный Telegram (MTProto) — ЗАБАНЕН, ждём перелогина
- `telegram-user-svc` (systemd, HTTP :8765) ОСТАНОВЛЕН (`systemctl stop/disable`) до успешного входа.
- Flood-ban спадает ~06:56 UTC 12.08 (09:56 МСК). **НЕ ретраить до бана.**
- План: ~07:30 UTC 12.08 один чистый code-login, затем `systemctl enable --now`.
- Инструменты агента: tg_send, tg_dialogs, tg_history (через плагин tg-user-tools).

## 🖼 Картинки
- Генерация по запросу: `calendar/image_gen.py` (Pollinations/Flux, бесплатно, без ключа).
- Мем-АВТОМАТИЗАЦИЯ УБРАНА 11.08 (meme_fetcher.py удалён, cron-задач нет).
- Gemini-ретушь: подключена, но упёрлась в квоту 429 — ждать.
- qwen-image-3-pro (OpenRouter): плагин есть, ключ не подхватывается — активный хвост.

## 🌐 Инфраструктура
- Сервер (основной, OpenClaw): VPS `vps-7182`/hiplet-109548, IP 138.124.180.178 (Франкфурт DE), Ubuntu 24.04, 2 vCPU/2GB/20GB, Tailscale hiplet-109548 = 100.113.115.17 (в тайлнете tail6a4baa). `vps-amnezia` (100.79.152.33) — отдельный узел, не рабочий.
- Сервер для личного VPN (AmneziaWG): старый 83.219.98.98 (оплачен до 10.11.2026). Старые серверы/IP забыты.
- Файрвол ufw: SSH22, tailnet 100.64.0.0/10, device-pair 18789 — только из tailnet; default deny in.
- Swap 2GB. Модель: deepseek/deepseek-chat (V4 Flash, прямой API).
- GitHub: приватный репо Dmgromov01/openclaw-workspace (main).

## 🔴 Активные хвосты (кратко)
1. TG re-login (после бана ~06:56 UTC 12.08)
2. Дайджест @de574574 (Екатерина) — после релогина
3. qwen-image-3-pro — ключ не подхватывается (auth sqlite)
4. `_collect_news` в orchestrator — заглушка
5. `orchestrator.py` всё ещё `import icloud_calendar` — перевести на gcal_reader
6. Добавление событий в Google Calendar не реализовано

> Если что-то перестало соответствовать реальности — **обнови этот файл** и MEMORY.md.
