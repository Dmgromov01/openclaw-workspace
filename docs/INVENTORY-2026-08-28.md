# Инвентарь машины и репозиториев

Снимок: **28.08.2026, ~09:00 UTC**. Секреты не включены.

Два репо, одна машина:

| Роль | Репо | На диске |
|---|---|---|
| OpenClaw-агент, скрипты, systemd-шаблоны | [Dmgromov01/openclaw-workspace](https://github.com/Dmgromov01/openclaw-workspace) `d499afb` | `/root/openclaw` |
| Сайт хаба (TanStack Start) | [Dmgromov01/atlas-green-pearl-dawn](https://github.com/Dmgromov01/atlas-green-pearl-dawn) `737602c` | `/root/atlas-green-pearl-dawn` |

---

## 1. Сервер

**Хост:** `hiplet-112102` (Tailscale `tail6a4baa.ts.net`)  
**OS:** Ubuntu 24.04, ядро `6.8.0-138-generic`  
**IP WAN:** `138.124.180.178` (Франкфурт)  
**Диск:** ~37% из 37.7 GB  
**RAM:** ~3.8 G + zram0 ~2 G  
**SSH:** root. Linger для root **выключен** (user-юниты не поднимаются после ребута).

### Порты (loopback / LAN)

| Порт | Кто | Снаружи |
|---|---|---|
| `127.0.0.1:18789` | `openclaw-gateway` (system) | только через nginx `https://gbkz.uk` (WSS) |
| `0.0.0.0:8091` | `r2d2-hub` vite preview | `https://hub.gbkz.uk` |
| `127.0.0.1:8765` | `telegram-user-svc` (python) | нет |
| `:8080` | **пусто** | Mini App снесён |
| `:22 :80 :443` | ssh / nginx / TLS | ufw: 22/80/443 + tailnet `100.64.0.0/10` |

**Не публиковать** `:18789` и `:8091` на WAN. Nginx — TLS-терминатор.

### Домены

| Хост | Куда |
|---|---|
| `gbkz.uk` | nginx → `127.0.0.1:18789` (OpenClaw Control UI / iPhone WSS) |
| `hub.gbkz.uk` | nginx → `:8091` (сайт хаба) |
| `dmkz.org` | заброшен, не использовать |
| Серт Let's Encrypt | до **17.11.2026**, `certbot.timer` |

### Systemd (живые)

| Юнит | Состояние | Заметки |
|---|---|---|
| `openclaw-gateway` | **system, enabled, Restart=always** | `OPENCLAW_NO_RESPAWN=1`. Файл: `/etc/systemd/system/openclaw-gateway.service` |
| `r2d2-hub` | **system, active**, `Restart=on-failure` | крутит **`.vercel/output`** (preset vercel, сборка 27.08 11:24). Ночью 28.08 падал на PGLite wasm, systemd поднял (restart counter 11) |
| `telegram-user-svc` | system | HTTP 8765 |
| user `openclaw-gateway` | **снят**, linger=no | не возвращать |
| `miniapp` | **снят** (28.08) | `:8080` не слушает |

Рестарт шлюза **только с SSH:** `systemctl restart openclaw-gateway` (без `--user`). Не через Telegram-агента.

### OpenClaw (живой конфиг, не в git)

Путь: `/root/.openclaw/openclaw.json`  
Версия: **OpenClaw 2026.7.1-2 (0790d9f)**

| Ключ | Значение |
|---|---|
| `gateway.reload.mode` | `off` |
| `gateway.controlUi.allowInsecureAuth` | `false` |
| `channels.telegram.dmPolicy` | `allowlist` |
| `channels.telegram.allowFrom` | `["1916536646"]` |
| `channels.telegram.commands.native` | `false` |
| чат / heartbeat | `deepseek/deepseek-v4-flash` |
| глубоко | `deepseek/deepseek-v4-pro` (fallback) |
| входящее фото | `deepseek/deepseek-v4-flash-vision-exp`, fallbacks пусто |
| `thinkingDefault` | `medium` |
| compaction | `keepRecentTokens=150000`, `notifyUser=true`, `recentTurnsPreserve=6` |
| exec | `mode=allowlist`, ask=off, telegram execApprovals=false |
| `tools.alsoAllow` | `message`, `group:messaging` |
| deny | `music_generate`, `video_generate` |
| агент `hub` | `tools.allow=[]` (семейный чат сайта) |
| агент `main` | `@Dmbotmy_bot` |

**Allowlist main (без `openclaw`):** ls cat head tail df journalctl date uname free zramctl mkdir mv tar gpg git ss curl echo + 3 opaque `=node-command:…`  
**Нельзя:** rm reboot systemctl loginctl systemd-run chmod chown ufw

Плагины шлюза (загружены ~8): device-pair, jina-tools, memory-core, openrouter, parallel, telegram, tg-user-tools.

### Telegram

| Бот | Роль |
|---|---|
| `@Dmbotmy_bot` (id 8675950544) | оператор → агент **main**. Кнопка = обычная ссылка `https://hub.gbkz.uk` |
| `@HubAlertsbot` (id 8915951913) | пейджер хаба / watchdog. Токен только в `.env` хаба |
| хозяин | `1916536646` `@Dm_GRM` |

WhatsApp закрыт. Mini App **удалён**.

### Cron

- `* * * * *` `/root/openclaw/services/loop-watchdog-cron.sh` — `:18789` и `:8765`, 3 провала → restart, антишторм 60 с, алерт HubAlertsbot
- `* * * * *` `/root/atlas-green-pearl-dawn/scripts/hub-watchdog-cron.sh` — хаб `:8091`
- бэкап: `/var/backups/r2d2` (задуман `scripts/hub-backup.sh` в репо хаба)

### Данные вне git

| Путь | Что |
|---|---|
| `/root/.openclaw/` | конфиг, credentials, sessions, exec-approvals.json |
| `/root/.openclaw/credentials/gcal/` | Google Calendar SA |
| `/root/.openclaw/credentials/cloudflare/r2.json` | R2, chmod 600 |
| `/root/atlas-green-pearl-dawn/.env` | токены хаба, OPENCLAW_*, PGLITE, Google, HubAlertsbot |
| `/var/lib/r2d2/pglite` | база хаба |
| `/root/atlas-green-pearl-dawn/.vercel/output` | **живая сборка хаба** (не в git). Не удалять без новой сборки |

### Известные дыры

1. Хаб работает с Nitro **vercel** preset через `vite preview`. Хрупко (ночной crash PGLite).
2. `r2d2-hub` = `Restart=on-failure` — чистый exit 0 не поднимет процесс.
3. Ключи в открытом `openclaw.json` (SecretRefs не делали).
4. В workspace git ещё лежит шаблон `services/miniapp.service` — код Mini App уже удалён, шаблон нет.
5. Хаб-репо всё ещё экспорт Grok App Builder (`PreviewHostBridge`, `/__grok/manifest`).

---

## 2. openclaw-workspace

**HEAD:** `d499afb` — `chore: do not track fat MEMORY dump` (28.08)  
**Клон:** `/root/openclaw`

Назначение: мозг агента `main`, watchdog, календарные скрипты, шаблоны юнитов. **Не** код сайта.

### Корень

```
.gitignore
AGENTS.md          — правила агента (не трогать шлюз/хаб-код)
DREAMS.md
HEARTBEAT.md       — диск >85%, иначе HEARTBEAT_OK
IDENTITY.md
MEMORY.md          — ~5.5k, не раздувать; дневники в memory/
README.md
SOUL.md
STATE.md           — живое состояние (частично отстаёт от этого файла)
TOOLS.md
USER.md            — Дмитрий, боты
backup-gbkz.uk-nginx-20260820.conf
healthcheck.sh
test_report.xlsx   — мусор, можно снести
```

**Снесены 28.08 (`e65a79c`, 422 файла):** `miniapp/`, `miniapp-next/`, `bot/miniapp_menu.py`, `update_bot_button.py`, `test_update_bot_button.py`, `tmp/*.pdf`, blueprint tar.

### Каталоги

```
bot/
  file_handler.py

calendar/                 — скрипты оператора (не сайт)
  gcal_reader.py          — Google Calendar, Europe/Moscow
  digest.py               — дайджест по источникам (не Google News)
  image_gen.py            — Pollinations
  image_editor.py
  bot_sender.py / tg_sender.py / ics_generator.py / command_parser.py
  README.md, package.json

docs/
  PROMPT-run6.md          — «не кормить бота»
  run6-root.sh / run6.md  — миграция шлюза, история
  context7-ref.md
  aiogram/  bot-blueprint/

hub/                      — заметки, не код сайта
memory/                   — YYYY-MM-DD.md; fat dump не трекать
openclaw_modules/
plugins/
  jina-tools/
reports/
scripts/
services/
  openclaw-gateway.service   — шаблон system-юнита (живой файл в /etc)
  r2d2-hub.service           — шаблон хаба
  miniapp.service            — ХВОСТ, удалить из git
  loop-watchdog.sh
  loop-watchdog-cron.sh
  disk-check.sh
  clawpatch-weekly.sh
  digest/
skills/
travel/
```

### Запреты агенту (из AGENTS / MEMORY)

Не править руками `openclaw.json`. Не рестартить gateway из Telegram. Не трогать код хаба, ufw, zram, Parallel, Context7, GitHub MCP, агент hub. Не возвращать Google как LLM/vision.

---

## 3. atlas-green-pearl-dawn (хаб)

**HEAD:** `737602c` — isolate hub OpenClaw sessions (27.08 11:22 UTC)  
**Клон:** `/root/atlas-green-pearl-dawn`  
**Стек:** TanStack Start + Vite 8 + React 19 + PGLite + Tailwind 4  
**`package.json` name:** всё ещё `app-builder-workspace` (экспорт Grok)

Сайт: погода, курсы, задачи, дайджест, переводчик, календарь (Google + остатки iCloud в коде), чат OpenClaw, PIN, админка.

### Корень

```
.gitignore          — .env, .vercel/output, screenshots, attachments
.grok/              — платформенный хлам Grok
AGENTS.md           — шаблон App Builder, не путать с /root/openclaw/AGENTS.md
OPENCLAW.md         — промпт деплоя; Mini App велено выключить (сделано)
README.md
eslint.config.mjs
package.json / package-lock.json
startup.sh          — grok-preview, на hiplet не используется
tsconfig.json
vite.config.ts
migrations/
public/             — лого, apple-touch, weather-icons; манифест ссылается на /__grok/…
scripts/            — hub-watchdog, hub-backup, migrate, grok-pwa-*
server/             — grok-pwa middleware
src/
```

### Маршруты `src/routes/`

| Файл | Экран |
|---|---|
| `__root.tsx` | оболочка, Gate, HubBoot, PreviewHostBridge, SW unregister |
| `index.tsx` | дом |
| `calendar.tsx` | календарь |
| `chat.tsx` | чат → шлюз, сессия `hub:<userId>`, агент `hub` |
| `digest.tsx` / `sources.tsx` | дайджест |
| `translate.tsx` | переводчик |
| `settings.tsx` | настройки, «проверить агента» |
| `admin.tsx` | админка |
| `archive.tsx` | архив задач |
| `fun.tsx` | развлечения |
| `rates.tsx` | курсы |

Чат: `src/lib/server/openclaw.server.ts`  
`tool_choice: none`, заголовок `x-openclaw-session-key: hub:<userId>`, `OPENCLAW_AGENT_ID=hub`, `OPENCLAW_MODEL=openclaw/hub`.

### Как крутится на машине

```
WorkingDirectory=/root/atlas-green-pearl-dawn
EnvironmentFile=.env
ExecStart=node node_modules/.bin/vite preview --host 0.0.0.0 --port 8091
Build Directory: .vercel/output
Nitro Preset: vercel
```

Это **не** `npm run preview` (тот идёт через `scripts/with-app-env.mjs`).

---

## 4. Кто с кем говорит

```
Telegram @Dmbotmy_bot  →  OpenClaw agent main  →  DeepSeek
Telegram @HubAlertsbot →  watchdog / хаб .env  (не агент)
Сайт hub.gbkz.uk       →  :8091 r2d2-hub  →  HTTP :18789  →  agent hub (без tools)
iPhone node            →  wss://gbkz.uk → nginx → :18789  (token)
```

---

## 5. Что сознательно не трогать

- код хаба без отдельного ТЗ
- ufw, zram, nginx bind
- `.vercel/output` пока нет новой node-сборки
- секреты в git
- второй gateway

## 6. Очередь (не срочно)

1. Пересобрать хаб не vercel-пресетом, `Restart=always`, потом снести `.vercel/output`
2. Удалить `services/miniapp.service` из openclaw-workspace
3. SecretRefs для ключей OpenClaw
4. Снести `test_report.xlsx`, хвосты `docs/aiogram`
5. Face ID / инвайты хаба — продукт
