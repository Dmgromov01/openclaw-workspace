# STATE.md — Актуальное состояние (НАПОМИНАЛКА)

> **Читай этот файл первым при старте/перед работой с календарём и интеграциями.**
> Здесь зафиксировано ЧТО СЕЙЧАС реально работает. Обновляй при каждом изменении.

## Календарь хаба — GOOGLE CALENDAR API (не iCloud)
- Новые работы с календарём — через Google Calendar / хаб. Это **не** Google как LLM.
- Аккаунт: `dmgromov03@gmail.com`, service-account вне git: `/root/.openclaw/credentials/gcal/`
- Скрипт чтения: `calendar/gcal_reader.py` (today / week / list --days N), даты Europe/Moscow.
- iCloud из .env хаба убран 27.08 как дубль.

## Модели (утвердил хозяин 27.08)
- Чат / heartbeat: `deepseek/deepseek-v4-flash`
- Глубоко: `deepseek/deepseek-v4-pro`
- Входящее фото: `deepseek/deepseek-v4-flash-vision-exp` (не Google, не CLI media)
- Генерация картинок: OpenRouter → Gemini Flash image
- Не возвращать Google в LLM / vision / fallback. Агент не крутит openclaw.json руками.

## Telegram
- Оператор: `@Dmbotmy_bot` → агент **main** (id 8675950544)
- Пейджер хаба: `@HubAlertsbot` → только алерты (id 8915951913), токен в .env хаба
- Хозяин: 1916536646 (@Dm_GRM)
- `telegram-user-svc` systemd, HTTP 127.0.0.1:8765, authorized = Дмитрий
- Mini App: disabled, :8080 не слушает. Кнопка в боте = обычная ссылка https://hub.gbkz.uk
- Токен @Dmbotmy_bot ротирован 24.08; в git не класть

## Инфраструктура
- Машина: hiplet (tail6a4baa.ts.net), Ubuntu 24.04, ядро 6.8.0-138-generic, RAM ~3.8G, zram0 ~2G
- Хаб: https://hub.gbkz.uk — standalone сайт, systemd `r2d2-hub` :8091
- OpenClaw WSS: gbkz.uk → nginx → 127.0.0.1:18789
- **Gateway:** цель run6 = system-юнит `openclaw-gateway` (до run6 был user-юнит user@0.slice)
- ufw WAN: 22/80/443 + tailnet 100.64.0.0/10 — не трогать
- MCP: GitHub + Context7 — оставлять. Parallel on. Perplexity off
- Агент hub: `tools.allow=[]` — не включать tools
- GitHub: Dmgromov01/openclaw-workspace (этот репо), Dmgromov01/atlas-green-pearl-dawn (хаб, код не трогать)

## Exec (run6)
- `tools.exec.mode=allowlist` (ask=off). Telegram execApprovals = false
- allowlist: ls cat head tail df journalctl date uname free zramctl mkdir mv tar gpg git ss curl openclaw
- вне списка → deny без кнопки /approve
- не security=full

## Watchdog
- хаб: cron каждую минуту, 3 провала → restart r2d2-hub
- шлюз (run6): `services/loop-watchdog-cron.sh` :18789 и :8765, 3 провала → restart, антишторм 60с, алерт HubAlertsbot
- бэкап: /var/backups/r2d2
- heartbeat 60m flash: диск >85% иначе HEARTBEAT_OK

## Хвосты
1. Run6 (gateway system + linger + watchdog шлюза + без апрувов + выжечь Google vision) — промпт в `docs/PROMPT-run6.md`
2. Дайджест @de574574 — по необходимости
3. Face ID / инвайты хаба — не делались
