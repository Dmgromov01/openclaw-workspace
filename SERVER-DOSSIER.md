# SERVER-DOSSIER.md — полная карта сервера hiplet-112102

> **Сгенерировано:** 2026-09-18, агентом Crestodian (main)
> **Метод:** снято с живой машины (`openclaw status`, `config`, ss, systemctl,
> docker, ls, cron) — не из памяти. Где состояние могло устареть — помечено.
> **Версия OpenClaw:** 2026.9.4 (`3a9d69d`)

---

## 1. Железо и ОС

| Параметр | Значение |
|---|---|
| Hostname | `hiplet-112102` |
| Роль | KVM-гость (VM), Ubuntu 24.04 LTS |
| Ядро | 6.8.0-139-generic (x64) |
| CPU | 2 vCPU |
| RAM | 3.8 GiB total, ~2.8 GiB used, ~1.1 GiB available |
| Swap | 4.0 GiB (занято 2.0 GiB) |
| Диск | `/dev/sda1`, 38 GB, **занято 31 GB (81%)**, свободно 7.3 GB — после чистки 18.09 |
| Uptime | 11 дней 15:27 |
| Load average | 0.43 / 0.17 / 0.13 |
| Внешний IP | 138.124.180.178 (VPS Франкфурт, DE) |
| Tailscale | `tail6a4baa.ts.net`, exposure **off** |
| Node.js | v24.21.0 |

Диск: **81%** (18.09 освобождено 3.3 GB: `_trash`, workspace-мусор, 4 старых бэкапа). Порог в `HEARTBEAT.md` — 80%. См. §12.

---

## 2. Что работает и что нет — сводка

### 2.1 Работающие приложения

| Приложение | URL | Backend | Проверено |
|---|---|---|---|
| **R2D2 Hub** (семейный хаб) | https://hub.gbkz.uk | `127.0.0.1:8091` | ✅ 200, `/healthz` → `{"status":"ok"}` |
| **NOVA** (personal hub) | https://nova.gbkz.uk | `127.0.0.1:8093` | ✅ 200, `/api/health` → `{"ok":true}` |
| **OpenClaw Control UI** | https://ui.gbkz.uk | `127.0.0.1:18789` | ✅ 200 |
| **SearXNG** (поиск) | `127.0.0.1:8080` | docker `searxng` | ✅ up 11 дней |
| **PostgreSQL** (NOVA) | `172.19.0.2:5432` | docker, pgvector | ✅ healthy, 11h |
| **Redis** (NOVA, BullMQ) | `172.19.0.3:6379` | docker | ✅ healthy, 11h |

### 2.2 Работает, но с оговоркой

| Приложение | Адрес | Что не так |
|---|---|---|
| **Oura callback** | `127.0.0.1:8092` | Отвечает `400` на `/` — это OAuth-callback, не сайт; сервис жив |
| **Telegram user svc** | `127.0.0.1:8765` | Отвечает `404` на `/` (нет такого маршрута), слушает нормально |

### 2.3 Неработающее / мёртвое

| Компонент | Состояние |
|---|---|
| **`miniapp.service`** | ❌ Мёртвый юнит-артефакт (Mini App заброшен, сайт = hub) |
| **BullMQ-воркер NOVA** | ❌ Не существует: `createMemoryWorker` не вызывается, юнита нет. Задачи лягут в `wait` молча |
| **fail2ban** | ✅ active | jail `sshd` (включён 18.09) |
| **OpenClaw health-таймеры (Oura)** | ✅ Работают (см. §7) — ранее стояли `inactive dead`, сейчас закрыто |

---

## 3. Сервисы systemd

### 3.1 Системные юниты

| Юнит | Порт | Статус | Что делает |
|---|---|---|---|
| `nginx.service` | 80, 443 | ✅ running | Reverse proxy перед всеми сайтами |
| `docker.service` | — | ✅ running | Контейнеры |
| `containerd.service` | — | ✅ running | Runtime контейнеров |
| `personal-hub.service` | 127.0.0.1:8093 | ✅ running, enabled | NOVA (Next.js) |
| `r2d2-hub.service` | 127.0.0.1:8091 | ✅ running | Семейный хаб (Nitro node-server) |
| `telegram-user-svc.service` | 127.0.0.1:8765 | ✅ running | Telegram user (MTProto/Telethon) |
| `ssh.service` | 22 | ✅ running | SSH |
| `cron.service` | — | ✅ running | Планировщик |
| `rsyslog`, `systemd-*`, `dbus`, `polkit`, `udisks2`, `multipathd` | — | ✅ running | Базовая ОС |
| `ModemManager`, `qemu-guest-agent`, `getty`, `serial-getty` | — | ✅ running | Виртуалка/консоль |

### 3.2 Пользовательские юниты (user, root)

| Юнит | Статус | Что делает |
|---|---|---|
| `openclaw-gateway.service` | ✅ running (pid 768387), enabled, `Restart=always` | Gateway OpenClaw |
| `health-morning.timer` / `.service` | ✅ active/waiting · service dead (ждёт) | Утренний отчёт Oura |
| `health-weekly.timer` / `.service` | ✅ active/waiting | Недельный тренд Oura |
| `health-monthly.timer` / `.service` | ✅ active/waiting | Месячный глубокий разбор Oura |
| `openclaw-health-check.timer` / `.service` | ✅ active/waiting | Ежедневная read-only проверка OpenClaw |

---

## 4. Порты (фактическое прослушивание)

~~~
127.0.0.1:8080    docker-proxy     → SearXNG (единственный опубликованный порт контейнера)
127.0.0.1:8091    MainThread       → r2d2-hub (Nitro)
127.0.0.1:8092    python3          → Oura callback
127.0.0.1:8093    next-server      → NOVA
127.0.0.1:18789   MainThread       → OpenClaw Gateway (+ [::1])
127.0.0.1:8765    python           → telegram-user-svc
0.0.0.0:80        nginx
0.0.0.0:443       nginx
0.0.0.0:22        sshd
127.0.0.53:53     systemd-resolved
~~~

Наружу (через ufw) открыты только **22, 80, 443** + tailnet `100.64.0.0/10`.
Остальные порты — loopback, снаружи недоступны.

---

## 5. Nginx и TLS

| Домен | Backend | Сертификат до |
|---|---|---|
| `gbkz.uk` | — | 2026-11-25 |
| `hub.gbkz.uk` | 127.0.0.1:8091 | 2026-11-25 |
| `ui.gbkz.uk` | 127.0.0.1:18789 | 2026-12-02 |
| `nova.gbkz.uk` | 127.0.0.1:8093 | 2026-12-17 |

Cloudflare proxy IP: `172.67.223.229`, `104.21.32.152`.
Все три сайта проверены снаружи → **200**; HTTP → HTTPS редирект настроен.
`certbot.timer` активен, автопродление работает.

---

## 6. Docker

### 6.1 Контейнеры

| Контейнер | Образ | Статус | Порты |
|---|---|---|---|
| `personal-hub-postgres-1` | `personal-hub/postgres:16-alpine-pgvector` | ✅ healthy, 11h | не опубликованы (internal net) |
| `personal-hub-redis-1` | `redis:7-alpine` | ✅ healthy, 11h | не опубликованы (internal net) |
| `searxng` | `searxng/searxng:latest` | ✅ up 11 дней | `127.0.0.1:8080→8080` |
| `openclaw-sbx-workspace-*` ×3 | `openclaw-sandbox:bookworm-slim` | ✅ up 14–37h | — (sandbox-сессии) |

### 6.2 Сети

~~~
personal_hub_backend   internal=true, subnet 172.19.0.0/16   ← NOVA
searxng_default        internal=false
bridge                 internal=false
~~~

**Ключевая находка:** `internal: true` **блокирует публикацию портов**. У postgres/redis
`HostConfig.PortBindings` заполнен, но `NetworkSettings.Ports = null` и `ss -tln` пусто.
Контраст — `searxng_default`: опубликован.

Поэтому вместо loopback-портов **закреплены IP**: postgres `172.19.0.2`,
redis `172.19.0.3` (через `ipv4_address` + `ipam.subnet`). Изоляция (`internal: true`)
сохранена, адреса стабильны при пересоздании контейнеров.

---

## 7. Планировщики

### 7.1 Системный crontab (root)

~~~
0  5 * * 1    /root/openclaw/services/clawpatch-weekly.sh
30 6 * * *    /root/openclaw/healthcheck.sh >> healthcheck.log
10 6,18 * * * /usr/bin/python3 /root/openclaw/travel/flight_api.py
35 6 * * *    /root/openclaw/services/disk-check.sh >> /var/log/disk-check.log
* * * * *     /root/openclaw/services/loop-watchdog-cron.sh
* * * * *     /root/atlas-green-pearl-dawn/scripts/hub-watchdog-cron.sh
15 3 * * *    /root/atlas-green-pearl-dawn/scripts/hub-backup.sh
*/5 * * * *   /root/atlas-green-pearl-dawn/scripts/hub-tick-cron.sh
45 6 * * *    /root/atlas-green-pearl-dawn/scripts/hub-backup-check.sh
~~~

### 7.2 OpenClaw cron (внутренние задачи)

| Задача | Расписание | Статус |
|---|---|---|
| Loop watchdog | каждую минуту | ✅ ok |
| Memory Dreaming Promotion | `0 3 * * *` | ✅ ok |
| `oura-health-evidence` | `30 7 * * *` Europe/Moscow | ✅ ok, модель `relaymodels/gpt-5.6-*` |
| Skill collection review ×4 (main/health/chat/groups) | каждые 7 дней | ⚠️ у `chat` — **error** |

### 7.3 systemd timers

Oura (morning/weekly/monthly) + `openclaw-health-check` — все активны.
Системные: certbot, apt-daily, logrotate, sysstat, dpkg-db-backup.

---

## 8. OpenClaw: как устроен

### 8.1 Расположение

| Что | Путь |
|---|---|
| Workspace агентов | `/root/openclaw` |
| Конфиг | `/root/.openclaw/openclaw.json` |
| State dir | `/root/.openclaw` |
| SQLite state | `/root/.openclaw/state/openclaw.sqlite` |
| Плагины (встроенные) | `/root/.openclaw/extensions/` |
| Плагины (кастомные) | `/root/.openclaw/plugins/`, `/root/openclaw/plugins/` |
| Память (вне репо) | `/root/openclaw-state/memory/` ← симлинк `memory` |
| Медиа | `/root/.openclaw/media/` |
| Логи | `/root/.openclaw/logs/`, `/tmp/openclaw/` |

Gateway: `ws://127.0.0.1:18789`, auth token, loopback + `[::1]`.
Второй gateway создавать запрещено.

### 8.2 Агенты

| Агент | Размер store | Назначение |
|---|---|---|
| **main** | 1.1 GB (725 MB sqlite) | Операторский агент Дмитрия |
| **chat** | 22 MB | Restricted-профиль для внешних пользователей |
| **groups** | 2.1 MB | Групповые чаты |
| **health** | 1.1 MB | Oura/health-пайплайн |
| **openclaw** | 632 KB | Служебный |
| `hub` | — | Каталог на диске есть, активным в конфиге не значится |
| `user-test` | — | Тестовый остаток |

Всего **76 сессий в 5 сторах**. Ownership = `explicit`.

### 8.3 Плагины

- **Встроенные:** `codex`, `composio`, `deepseek`, `diffs`, `expedia-openclaw`, `memory-lancedb`, `tokenjuice`
- **Кастомные:** `tg-user-tools`, `workboard`, `agent-effectiveness`, `bot-access-command`, `jina-tools`
- **Отключены:** `google` (правило: не возвращать как LLM/vision/fallback), `perplexity`, `reef`

### 8.4 Skills

В `/root/openclaw/skills/` — установленные; с ClawHub — `aviasales-flights`,
`bot-access-control`, `caldav-calendar` (+ `.clawhub/origin.json`).
*Точное число skills в этом проходе не пересчитывал — `openclaw skills list` не запускал.*

---

## 9. Модели: что, как подключено, где используется

### 9.1 Провайдеры

| Провайдер | Base URL | API | Ключ |
|---|---|---|---|
| **deepseek** | `https://api.deepseek.com` | openai-completions | ✅ set |
| **relaymodels** | `https://api.relaymodels.com/v1` | openai-completions | ✅ set |
| **openrouter** | `https://openrouter.ai/api/v1` | openai-completions | ✅ set |
| **jina** | `https://api.jina.ai/v1` | openai-completions | ✅ set (embeddings) |
| **openai** | — (через Codex runtime) | openai-responses | ✅ set |

Ключи в конфиге **плейнтекстом**; в выводе редактируются как `__OPENCLAW_REDACTED__`.
Миграция на SecretRef **не выполнена**.

### 9.2 Дефолты (`agents.defaults`)

~~~
model.primary          relaymodels/deepseek-v4.1-flash
model.fallbacks        ["deepseek/deepseek-flash"]
utilityModel           deepseek/deepseek-flash
imageModel.primary     deepseek/deepseek-flash
mediaModels.image      openrouter/openai/gpt-5.4-image-2
                       ↳ fallback: openrouter/google/gemini-3.1-flash-image-preview
mediaModels.video      openrouter/google/veo-3.1-lite
~~~

Текущая сессия запинена на `relaymodels/deepseek-v4.1-flash`;
конфиг-дефолт для новых сессий — `deepseek/deepseek-flash`.

### 9.3 Политика моделей

~~~
allow: deepseek/deepseek-v4-flash, deepseek/deepseek-v4-pro,
       deepseek/deepseek-v4-flash-vision-exp, deepseek/deepseek-flash,
       deepseek/deepseek-chat, relaymodels/*, openrouter/*
~~~

### 9.4 Живой каталог (`openclaw models list`)

| Модель | Input | Ctx | Тег |
|---|---|---|---|
| `deepseek/deepseek-chat` | text | 131k | |
| `deepseek/deepseek-flash` | text+image | 1000k | **default, image, alias:DeepSeek** |
| `deepseek/deepseek-v4-flash` | text | 1000k | configured |
| `deepseek/deepseek-v4-flash-vision-exp` | text+image | 1000k | configured |
| `deepseek/deepseek-v4-pro` | text | 1000k | |
| `openrouter/google/gemini-3.1-flash-image-preview` | text+image | 66k | |
| `openrouter/google/veo-3.1-lite` | text | 200k | видео |
| `openrouter/openai/gpt-5.4-image-2` | text+image | 272k | картинки |
| `openrouter/auto` | text | 200k | |
| `openrouter/qwen/qwen-image-3-pro` | text | 33k | |
| `openrouter/z-ai/glm-5.3-flash` | text | 131k | |
| `relaymodels/deepseek-v4-pro` | text | — | |
| `relaymodels/deepseek-v4.1-flash` | text | — | fallback#1 |
| `relaymodels/gpt-5.6-sol` | text | — | |
| `relaymodels/kimi-k2.7-code` | text | — | |
| `relaymodels/qwen3.8-max-cursor` | text+image | 1000k | |

**Codex-биндинг:** `openai/*` маршрутизируется через runtime `codex`
(`agents.defaults.models["openai/*"].agentRuntime.id = "codex"`).

**V4.1 Flash:** legacy-имена `deepseek-v4-flash` и `deepseek-v4-flash-vision-exp`
обслуживаются той же V4.1 Flash; запросы к `deepseek-v4-pro` с 14.09.2026
маршрутизируются на V4.1 Flash.

---

## 10. Файлы приложений на сервере

### 10.1 NOVA (`personal-hub`)

~~~
/srv/personal-hub/
├── app/                     Next.js 16.2.6, App Router
│   ├── .env                 DATABASE_URL, REDIS_URL, ENCRYPTION_KEY, NODE_ENV
│   ├── src/app/api/…        37 маршрутов (auth, calendar, channels, digest,
│   │                        google, health, openclaw, oura, profile, security)
│   ├── src/components/      nova-dashboard, calendar-view, digest-view,
│   │                        health-view, health-analysis, openclaw-view,
│   │                        security-view, currency-card, auth-screen
│   ├── src/lib/             auth, crypto, queue, memory, openclaw, llm, pubmed,
│   │                        totp, rate-limit, google-drive, ics, ingest…
│   ├── src/db/schema.ts     41 export — 20 таблиц
│   └── db/migrations/       SQL-миграции
├── infra/                   docker-compose (postgres + redis, ipam, закреплённые IP)
├── secrets/                 0700: device-identity.json, device-token.json (0600)
└── backups/                 pg_dump, напр. nova-pre-pairing-*.dump
~~~

**Таблицы `personal_hub` (20):**
`audit_logs, calendar_events, calendar_sources, channels, currency_rates,
digest_items, google_connections, health_analyses, kg_assertions, kg_entities,
memory_documents, memory_summary_checkpoints, openclaw_bot_users, openclaw_configs,
openclaw_events, oura_connections, oura_metrics, rate_buckets, sessions, users`

**UX NOVA:** единая страница `page.tsx` + вкладки-компоненты —
Dashboard, Calendar, Digest, Health (+analysis), OpenClaw, Security, Currency.

### 10.2 R2D2 Hub

~~~
/root/atlas-green-pearl-dawn/
├── src/routes/      13 маршрутов: index, chat, calendar, digest, health,
│                    openclaw, settings, admin, sources, archive, activity,
│                    status, translate
├── src/components/  activity, admin, auth, calendar, chat, digest, health,
│                    home, settings, status, shell + lock-screen, onboarding…
├── src/lib/         логика
├── scripts/         hub-watchdog-cron.sh, hub-backup.sh, hub-tick-cron.sh,
│                    hub-backup-check.sh
└── .env             TELEGRAM_*, AI_KEY_SECRET, OPENCLAW_*, PGLITE_DATA_DIR,
                     GOOGLE_CALENDAR_*
~~~

Стек: TanStack Start/Router/Query/Table + Nitro node-server.
БД: **PGLite** (`/var/lib/r2d2/pglite`).

### 10.3 Workspace агента (`/root/openclaw`)

~~~
AGENTS.md SOUL.md IDENTITY.md USER.md MEMORY.md STATE.md ARCHITECTURE.md
HEARTBEAT.md DREAMS.md README.md SERVER-DOSSIER.md
memory -> /root/openclaw-state/memory   (симлинк, вне репо)
bin/       operator-скрипты (bot-access, openclaw-web-tools, safe-sqlite-edit,
           health-*, aviasales-flights-operator)
scripts/   make_video.py и др.
skills/    установленные ClawHub-скиллы
plugins/   кастомные плагины
services/  clawpatch-weekly.sh, disk-check.sh, loop-watchdog-cron.sh
calendar/  gcal_reader.py, gcal_auth.py, digest.py, bot_sender.py
travel/    flight_api.py
workspace/ health/ (Oura-пайплайн, analytics, deploy/, analysis/, memory/)
docs/ tests/ hub/ media/ reports/ archive/ _archive/ _scratch/
_trash/ _trash_/ venv/ logs/
~~~

---

## 11. Безопасность

| Параметр | Состояние |
|---|---|
| **ufw** | ✅ active, default deny incoming; открыты 22/80/443 + tailnet |
| **SSH (эффективно)** | ✅ `permitrootlogin without-password`, `passwordauthentication no`, `pubkeyauthentication yes` |
| **`sshd_config.d/`** | ⚠️ конфликтующие файлы (`50-cloud-init` разрешает пароли, `99/00-openclaw-hardening` запрещают). Эффективно побеждает hardening (`sshd -T`), но мусор стоит убрать |
| **fail2ban** | ✅ active, jail sshd (18.09) |
| **Секреты** | ✅ 8/8 путей → `${VAR}` (env-substitution); значения в `/root/.openclaw/secrets.env` (600) + systemd drop-in `20-secrets-env.conf`; плейнтекста в конфиге нет (18.09). Активация — рестарт gateway |
| **Exec-политика** | allowlist, `ask=on-miss`, `askFallback=deny`; вне allowlist — deny |
| **Hub agent** | `tools.allow=[]` |
| **Gateway bind** | 127.0.0.1 (loopback) |
| **Root login** | Только по ключу |

---

## 12. Диск: куда уходит 34 GB

| Путь | Размер |
|---|---|
| `/root/openclaw/venv` | 424 MB |
| `2026-09-06T11-28-49…backup.tar.gz` | 227 MB |
| `2026-09-06T11-22-02…backup.tar.gz` | 227 MB |
| `/root/openclaw/_trash` | 137 MB |
| `/root/openclaw/media` | 37 MB |
| `/root/openclaw/workspace` | 34 MB |
| `/root/openclaw/_trash_` | 28 MB |
| `/root/*openclaw-backup.tar.gz` | **394 MB** (только 17.09; остальные удалены 18.09) |
| `/root/backups/` | локальные зашифрованные копии (age) |

**Кандидаты на освобождение:** старые бэкапы в `/root` и `/root/_trash` (~2 GB),
два бэкапа от 06.09 в workspace (454 MB), `_trash`/`_trash_` (165 MB).
Ничего не удаляю без команды.

---

## 13. Проблемы: полный список

### 🔴 Требует внимания
1. **BullMQ-воркер NOVA нельзя запустить** — `loadTranscriptWindow` = fail-closed заглушка (таблица транскрипта неизвестна) и **реализации `Embedder` нет**. Задачи копятся в `wait` молча (см. §2.3)

### 🟡 Средние
3. **`skill-collection-review` у агента `chat`** — статус `error`
4. **Offsite-бэкап без `REMOTE`** — локальные age-копии есть, выгрузки наружу нет
5. **Хвосты `telegram-user-svc`** (404 на `/`) и **`8092`** (400) — вероятно ожидаемо; проверка = `ss -ltn` + `journalctl --since -1h`

### ⚪ Косметика
6. Каталоги агентов `hub`, `user-test` — остатки

### ✅ Закрыто 18.09
- Диск 90% → **81%** (чистка 3.3 GB)
- **fail2ban** включён (jail sshd)
- Мониторинг ресурсов + logrotate + инвентарь skills
- `miniapp.service`, `.bak` — убраны
- **Секреты**: 8/8 credential-путей → `${VAR}`, env-файл + systemd drop-in, плейнтекста нет
- **Offsite-backup**: скрипт + age + cron 03:40 (локальные шифр-копии работают; нужен `REMOTE_BACKUP`)

---

## 14. Приложения: подробности

### 14.1 R2D2 Hub — что умеет

Разделы: `index`, `chat` (чат через gateway), `calendar`, `digest`, `health`
(Oura + PubMed + AI), `openclaw`, `sources`, `archive`, `activity`, `status`,
`translate`, `settings`, `admin`.

Особенности: admin = первый посетитель пустого хаба; auth через имя → PIN →
Face ID/биометрия; invite-система; AI только при `ai_mode='shared'` **и**
`allow_global_ai=true`.

### 14.2 NOVA — что умеет

Разделы: Dashboard, Calendar, Digest, Health + Health Analysis, OpenClaw,
Security, Currency.

Из API: локальная auth (login/register/logout/mfa/demo), 2FA, биометрия, PIN,
аудит, календарь + источники + sync, каналы, валюты, дайджест + refresh,
Google (connect/callback/disconnect/status/backup), Oura ({,sync,sample}),
health analysis, OpenClaw (config/feed/status/tools.invoke/users/pairing), profile.

**Хранилища:** PostgreSQL (20 таблиц) + Redis (BullMQ). `ENCRYPTION_KEY` для
AES-256-GCM. **Воркер очередей не запущен** (см. §2.3).

---

## 15. Хронология ключевых изменений

| Дата | Событие |
|---|---|
| 27.08 | R2D2 Hub развёрнут на hub.gbkz.uk, nginx + Let's Encrypt; перевод на системный юнит + watchdog |
| 31.08–01.09 | TZ-CLOSEOUT / TZ-CANON / TZ-PROOF (см. `docs/`) |
| 06.09 | OpenClaw 2026.9.1→9.2; бэкап-архивы в workspace |
| 10.09 | Exec починен, `image_generate` протестирован |
| 11.09 | OpenClaw 2026.9.4; Oura sync, аудит сервера |
| 12.09 | Composio установлен |
| 14.09 | Память вынесена в `/root/openclaw-state/memory` (симлинк) |
| **17–18.09** | **NOVA развёрнут: nova.gbkz.uk, `personal-hub.service` :8093, 20 таблиц** |
| **18.09** | **Git sync: `f843ad3d`, `0861bffa`, `27f8bbc6`; ARCHITECTURE.md дополнен** |
| **18.09** | **Ops: диск 90→81%, fail2ban, resource-check + cron, logrotate, swappiness=10, OOM drop-ins, offsite-backup + age** |

---

## 16. Рекомендации (по приоритету)

1. **Воркер BullMQ NOVA** — реализовать `loadTranscriptWindow` под реальную таблицу транскрипта и `Embedder` (1536-dim); без них воркер не поднимается
2. **Активировать секрет-миграцию** — рестарт gateway по SSH (`~/.openclaw/secrets.env` + drop-in уже готовы)
3. **Задать `REMOTE_BACKUP`** — включить реальную выгрузку offsite (rclone настроен)
4. **Разобрать `skill-collection-review` error** у агента `chat`
5. **Проверить живость `telegram-user-svc`** (8765) и Oura callback (8092)
6. **`openclaw sessions prune` + `VACUUM`** SQLite — при остановленном gateway
7. **Убрать остатки** агентов `hub`/`user-test`

---

*Файл: `/root/openclaw/SERVER-DOSSIER.md`. Собран с живой машины 2026-09-18.
При расхождении с `STATE.md` / `CURRENT_SYSTEM_STATE.md` — сверяться с фактическим
состоянием сервера, а не с памятью.*



