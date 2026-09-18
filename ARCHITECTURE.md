# Архитектура сервера OpenClaw — hiplet-112102

> **Дата актуализации:** 2026-09-14  
> **Версия OpenClaw:** 2026.9.4 (3a9d69d)  
> **Хост:** hiplet-112102 (VPS Франкфурт DE, IP 138.124.180.178)  
> **Tailscale:** tail6a4baa.ts.net (exposure off)

---

## 1. Аппаратная и системная база

| Параметр | Значение |
|---|---|
| OS | Ubuntu 24.04 LTS |
| Ядро | 6.8.0-139-generic (x64) |
| Node.js | v24.21.0 |
| RAM | ~3.8 GiB |
| Swap | zram0 (zstd, ~1.9 GiB, PRIO 100) |
| Диск | /dev/sda1, 38 GiB |
| Workspace | `/root/openclaw` |
| Конфиг OpenClaw | `/root/.openclaw/openclaw.json` |
| State dir | `/root/.openclaw` |
| SQLite state | `/root/.openclaw/state/openclaw.sqlite` |

**Swapfile не ставить** — swap только через zram.

---

## 2. Сервисы и порты

### 2.1 Системные юниты

| Юнит | Тип | Порт | Статус | Назначение |
|---|---|---|---|---|
| `openclaw-gateway.service` | user | 127.0.0.1:18789 | ✅ running (pid 523589) | Gateway OpenClaw, WebSocket + HTTP API |
| `r2d2-hub.service` | system | 127.0.0.1:8091 | ✅ running | Семейный хаб hub.gbkz.uk |
| `telegram-user-svc.service` | system | 127.0.0.1:8765 | ⚠️ молчит с 27.08 | Пейджер Telegram (инбаунд-аудио) |
| `oura-callback.service` | system | 127.0.0.1:8092 | ✅ running | Oura OAuth2 callback + sync |
| `miniapp.service` | system | — | ❌ мёртвый | Mini App (заброшен, сайт = hub.gbkz.uk) |
| `openclaw-health-check.service/.timer` | user | — | ⚠️ не включены | Health-таймеры Oura (morning/weekly/monthly) |

### 2.2 Nginx (reverse proxy)

| Домен | Backend | Примечание |
|---|---|---|
| `hub.gbkz.uk` | 127.0.0.1:8091 | Cloudflare proxy → nginx → r2d2-hub |
| `ui.gbkz.uk` | 127.0.0.1:18789 | Cloudflare proxy → nginx → OpenClaw Gateway (Control UI) |

Cloudflare proxy IPs: `172.67.223.229`, `104.21.32.152`.

### 2.3 Мёртвые/забытые артефакты

- `miniapp.service` — мёртвый юнит, можно удалить
- `openclaw-gateway.service.bak` — артефакт обновления, можно удалить
- `/root/_trash/ideal-20260911/` — бэкапы аудита (audit-2103-before-repairs.tgz, 2.4 MB)

---

## 3. Архитектура памяти OpenClaw

### 3.1 Файловая структура памяти

```
/root/openclaw/
├── MEMORY.md              # Главная память (только main-сессия)
├── USER.md                # Профиль владельца (Дмитрий)
├── SOUL.md                # Персона/тон ассистента
├── IDENTITY.md            # Имя, роль, эмодзи
├── AGENTS.md              # Правила workspace, границы, constraints
├── TOOLS.md               # Операционная шпаргалка (exec, модели, сервисы)
├── ARCHITECTURE.md        # ← этот файл
├── memory/
│   ├── profile.md         # Системный профиль (сервер, стек, модели)
│   ├── YYYY-MM-DD.md      # Дневники сессий (ежедневные)
│   ├── dreaming/          # Сны (light/deep) — генерируются автоматически
│   │   ├── light/YYYY-MM-DD.md
│   │   └── deep/YYYY-MM-DD.md
│   └── .dreams/           # Raw dream data (session-corpus, не коммитить)
└── _trash/                # Бэкапы, удалённые файлы (не коммитить)
```

### 3.2 Как работает память

| Компонент | Описание |
|---|---|
| **MEMORY.md** | Долгосрочная память главной сессии. Читается при старте. Обновляется вручную или через dreaming. |
| **USER.md** | Директивы владельца: стиль ответов, контекст, правила. Приоритет выше SOUL.md. |
| **SOUL.md** | Persona: тон, границы, атмосфера. «Не чат-бот, а личность». |
| **AGENTS.md** | Runtime-канон: что нельзя трогать, exec-политика, границы сервисов. |
| **Дневники** | `memory/YYYY-MM-DD.md` — хронология работы за день. Не коммитить runtime dreams/sessions/reports. |
| **Dreaming** | Автоматическая консолидация памяти ночью (`0 3 * * *`). Light sleep = кандидаты в staged; Deep sleep = принятые решения. |
| **memory_search** | Семантический поиск по MEMORY.md, USER.md, memory/*.md. Обязательно перед ответами о prior work. |
| **memory_get** | Точное чтение фрагментов из файлов памяти по path#line. |
| **Project scoping** | Записи в memory привязываются к репозиторию через `<!-- project: github.com/Dmgromov01/openclaw-workspace -->`. |
| **Компактизация** | При превышении контекста сессия компактизируется в summary. Теряются детали, остаются решения и TODO. |

### 3.3 Политика памяти

- `.gitignore`: `memory/dreaming/`, `.dreams/`, `*.db`, `openclaw.json`, `_trash/`, `workspace-*` — **не коммитить**.
- MEMORY.md — только для главной сессии Дмитрия.
- Дневники не коммитить (runtime data).
- Секреты в ответы и в git **не писать**.

---

## 4. Модельные провайдеры

### 4.1 Текущие провайдеры

| Провайдер | Base URL | API | Модели | Статус |
|---|---|---|---|---|
| **deepseek** | api.deepseek.com | openai-completions | v4-flash, v4-pro, chat, reasoner, v4-flash-vision-exp, flash (V4.1) | ✅ Работает |
| **openrouter** | openrouter.ai/api/v1 | openai-completions | auto, qwen-image-3-pro, glm-5.3-flash | ✅ Работает |
| **relaymodels** | api.relaymodels.com/v1 | openai-completions | gpt-5.6-luna, deepseek-v4-flash, deepseek-v4-pro, kimi-k2.7-code, qwen3.8-max | ✅ Работает |
| **openai** | (через Codex runtime) | openai-responses | gpt-5.6, gpt-5.5, gpt-5.6-sol/luna/terra, gpt-6-astra | ⚠️ Частично (см. проблемы) |
| **jina** | api.jina.ai/v1 | openai-completions | jina-embeddings-v3 | ✅ Embeddings only |

### 4.2 Дефолтные модели

| Назначение | Модель | Fallback |
|---|---|---|
| Чат (default) | `deepseek/deepseek-v4-pro` | — |
| Текущая сессия | `relaymodels/kimi-k2.7-code` | `deepseek/deepseek-v4-pro` |
| Image generation | `openrouter/openai/gpt-5.4-image-2` | `openrouter/google/gemini-3.1-flash-image-preview` |
| Vision | `deepseek/deepseek-flash` | — |

### 4.3 Model Policy

```
agents.defaults.modelPolicy.allow:
  - deepseek/deepseek-v4-flash
  - deepseek/deepseek-v4-pro
  - deepseek/deepseek-v4-flash-vision-exp
  - deepseek/deepseek-flash
  - deepseek/deepseek-chat
  - relaymodels/*
  - openrouter/*
```

### 4.4 Image Generation (image_generate)

**Статический каталог** (захардкожен в OpenClaw, не расширяется через конфиг):

| Провайдер | Модели | Режимы |
|---|---|---|
| openai | gpt-image-2, gpt-image-2.5-flare/sunburst, gpt-image-1.5/1/1-mini | generate, edit |
| openrouter | gemini-3.1-flash-image-preview, gemini-3-pro-image-preview, gpt-5.4-image-2 | generate, edit |

**Важно:** 53 модели доступны на OpenRouter Images API (`/api/v1/images`), но OpenClaw знает только 3 из них. Seedream 5.0 Pro, FLUX, Recraft и др. **недоступны** через `image_generate` — только через прямой curl/skill.

---

## 5. Плагины

### 5.1 Включённые плагины

| Плагин | Статус | Назначение |
|---|---|---|
| deepseek | ✅ enabled | DeepSeek provider |
| openrouter | ✅ enabled | OpenRouter provider |
| openai | ✅ enabled | OpenAI provider (personality: on) |
| codex | ✅ enabled | Codex runtime (dynamic tools: searchable) |
| telegram | ✅ enabled | Telegram channel |
| tg-user-tools | ✅ enabled | Telegram user tools (custom plugin) |
| memory-core | ✅ enabled | Memory + dreaming (cron: 0 3 * * *) |
| active-memory | ✅ enabled | Active memory management |
| browser | ✅ enabled | Browser automation |
| composio | ✅ enabled | External apps integration (hook-only, allowConversationAccess) |
| diffs | ✅ enabled | Diff viewer (allowConversationAccess) |
| tokenjuice | ✅ enabled | Token tracking |
| workboard | ✅ enabled | Task board |
| parallel | ✅ enabled | Parallel search MCP |
| searxng | ✅ enabled | SearXNG search (baseUrl: 127.0.0.1:8080) |
| jina-tools | ✅ enabled | Jina embeddings/tools (custom plugin) |
| agent-effectiveness | ✅ enabled | Agent effectiveness tracking (custom plugin) |
| bot-access-command | ✅ enabled | Bot access control (custom plugin) |
| device-pair | ✅ enabled | Device pairing |
| expedia-openclaw | ✅ enabled | Expedia travel adapter (synthetic_mode: false) |

### 5.2 Отключённые плагины

| Плагин | Причина |
|---|---|
| google | Отключён (правило: «Не возвращать Google как LLM/vision/fallback») |
| perplexity | Отключён (правило: Perplexity off) |
| reef | Отключён |

### 5.3 Custom plugins (load paths)

```
/root/.openclaw/plugins/tg-user-tools
/root/openclaw/plugins/jina-tools
/root/openclaw/plugins/agent-effectiveness
/root/openclaw/plugins/bot-access-command
```

### 5.4 Предупреждения

- **composio**: hook-only compatibility path, не мигрирован на explicit capability registration
- **Skills**: 24 eligible, 5 missing
- **Plugin compatibility**: 1 warning (composio)

---

## 6. Skills (навыки)

### 6.1 Доступные skills

| Skill | Описание |
|---|---|
| add-model-provider | Добавление model provider |
| bot-access-control | Управление доступом Telegram (owner 1916536646) |
| browser-automation | Browser control |
| caldav-calendar | CalDAV синхронизация (vdirsyncer + khal) |
| clawhub | Поиск/установка skills из ClawHub |
| cloud-image-bake | Cloud Worker image baking |
| composio | External apps через Composio CLI |
| configure-channel | Настройка chat channels |
| control-ui | Control UI operations |
| diagnose-gateway | Диагностика gateway |
| diagram-maker | SVG/HTML диаграммы |
| diffs | Diff viewer |
| flights | Aviasales/Travelpayouts авиабилеты |
| healthcheck | Аудит безопасности хоста |
| node-connect | Диагностика подключения нод |
| node-inspect-debugger | Node.js debugging |
| openclaw-agent-roster-changes | Управление агентами |
| r2d2-hub | Контракт развёртывания хаба |
| skill-creator | Создание/ревью skills |
| taskflow | Approval-gated workflows |
| taskflow-inbox-triage | Inbox triage preview |
| tmux | Tmux session control |
| travel-search | EG Travel adapter (hotels/flights) |
| weather | Погода (web_fetch + wttr.in) |

### 6.2 Недостающие skills (5 missing)

Определяются OpenClaw автоматически. Список меняется при обновлениях.

---

## 7. Агенты

| Агент | Сессий | Последняя активность | Store |
|---|---|---|---|
| **main** | 57 | 2m ago | ~/.openclaw/agents/main/agent/openclaw-agent.sqlite |
| **chat** | 17 | 23m ago | ~/.openclaw/agents/chat/agent/openclaw-agent.sqlite |
| **groups** | 1 | 3d ago | ~/.openclaw/agents/groups/agent/openclaw-agent.sqlite |
| **health** | 1 | 2d ago | ~/.openclaw/agents/health/agent/openclaw-agent.sqlite |
| **openclaw** | 0 | unknown | ~/.openclaw/agents/openclaw/agent/openclaw-agent.sqlite |

**Всего:** 5 агентов, 76 сессий, 2 активных за последние 30 минут.

---

## 8. Каналы связи

### 8.1 Telegram

- **Статус:** ON / OK
- **Токен:** sha256:4c220679, len 46
- **Аккаунт:** default (credential available in gateway runtime)
- **Allowlist:** 1916536646 (Дмитрий), 8335493342
- **Бот:** @Dmbotmy_bot (агент main)
- **Пейджер:** @HubAlertsbot (только алерты)

### 8.2 WebChat

- **Dashboard:** http://127.0.0.1:18789/
- **External URL:** https://ui.gbkz.uk (через nginx + Cloudflare)

---

## 9. Интеграции

### 9.1 Oura Ring

- **Callback сервис:** :8092, OAuth2 flow
- **Sync скрипт:** `/root/openclaw/workspace/health/scripts/oura_sync.py`
- **База данных:** `/root/openclaw/workspace/health/data/oura.db` (SQLite, таблица `oura_raw`)
- **Эндпоинты:** 18 коллекций (heartrate, sleep, workout, daily_activity, readiness, resilience, spo2, stress, vO2_max и др.)
- **Первая выкачка:** 103 544 строки за 30 дней (2026-08-12..09-11), errors={}
- **Health analytics:** `/root/openclaw/workspace/health/scripts/analytics.py` (v2.1)
- **Таймеры:** morning/weekly/monthly — установлены в `~/.config/systemd/user/`, но **НЕ включены**

### 9.2 Composio

- **Плагин:** @composio/composio@0.1.0 (~/.openclaw/extensions/composio)
- **CLI:** /root/.composio/cli/composio (@composio/cli@0.4.1)
- **Авторизация:** managed auth/OAuth (не API-ключ)
- **Назначение:** Внешние приложения (email, calendar, CRM, source control)
- **Статус:** Установлен 12.09, permissions + smoke-test **не завершены**

### 9.3 CalDAV Calendar

- **Skill:** caldav-calendar (vdirsyncer + khal)
- **Bins:** apt install vdirsyncer khal выполнен ✅
- **Конфиги:** vdirsyncer/khal **НЕ созданы** (TODO с 06.09)

### 9.4 Travel

- **Expedia plugin:** expedia-openclaw (enabled, synthetic_mode: false)
- **Travel search skill:** EG Travel adapter
- **Flights skill:** Aviasales/Travelpayouts (TRAVELPAYOUTS_TOKEN записан владельцем 06.09)

---

## 10. Exec-политика и безопасность

### 10.1 Exec configuration

```
tools.exec.mode = auto
Effective (SQLite): security=allowlist, ask=on-miss, askFallback=deny
```

### 10.2 Allowlist

```
ls cat head tail df journalctl date uname free zramctl mkdir mv tar gpg git ss curl openclaw python3
```

### 10.3 Ограничения

- Headless-запуски НЕ могут ждать интерактивного approval → всё вне allowlist = deny
- Auto-review режет `rm -rf` в /root (risk=high), в /tmp пропускает
- Deny: `systemctl reload nginx`, `nginx -t`, `cd X && cmd`, pipes/redirects
- `systemctl` вне allowlist — рестарты сервисов только владельцем
- ufw, zram, bind gateway (127.0.0.1:18789) — не трогать без прямого ТЗ

### 10.4 Secrets audit

- **15 plaintext findings** (gateway.auth.token, apiKey провайдеров, channels.telegram.botToken и др.)
- **Unresolved:** 0
- **Миграция на SecretRef:** НЕ выполнена (запрещено ТЗ без прямого запроса)

---

## 11. Проблемы и неработающее

### 11.1 Критические

| Проблема | Описание | Статус |
|---|---|---|
| **Telegram бот молчит** | Codex runtime error: «Codex session policy handoff failed: Codex did not confirm unloading its previous configuration». Исходящие замерли. | 🔴 Требует `/codex stop` + `/codex resume` или рестарт gateway |
| **OpenAI Astra недоступна** | `model_not_found` для `gpt-6-astra` — у проекта нет доступа. 47 отказов. | 🔴 Хозяин: «про Codex забываем» |
| **Dead-letter queue** | Outbound: 1, session: 1, inbound telegram: 3. Oldest: 26 дней назад. | 🟡 Нужно разобрать |

### 11.2 Средние

| Проблема | Описание | Статус |
|---|---|---|
| **Oura таймеры не включены** | morning/weekly/monthly timers установлены, но не enabled | 🟡 Требуется `systemctl --user enable --now` (владелец) |
| **Composio smoke-test** | Permissions + smoke-test после входа не завершены | 🟡 |
| **CalDAV конфиги** | vdirsyncer/khal bins установлены, конфиги не созданы | 🟡 TODO с 06.09 |
| **Plaintext secrets** | 15 секретов в открытом виде в конфиге | 🟡 Миграция на SecretRef нужна |
| **Stale Codex state** | Stale Codex и OpenAI session routing state в agent:main:main | 🟡 |
| **Agent health warning** | «Memory system not found in workspace» | 🟡 |
| **Update failed** | `openclaw update failed: unknown reason` (в status) | 🟡 Версия 2026.9.4 установлена, но update run помечен как failed |

### 11.3 Низкие / косметические

| Проблема | Описание | Статус |
|---|---|---|
| **miniapp.service** | Мёртвый юнит, Mini App заброшен | ⚪ Можно удалить |
| **openclaw-gateway.service.bak** | Артефакт обновления | ⚪ Можно удалить |
| **telegram-user-svc молчит** | Последнее сообщение 27.08 (~18 дней) | ⚪ Отдельная задача |
| **.env хаба** | `OPENCLAW_AGENT_ID=hub` (агент hub удалён, должен быть `chat`) | ⚪ Ждёт решения владельца |
| **Legacy Browser Relay auth** | Включён legacy auth | ⚪ |
| **Jina/Brave ключ не в env** | Поиск public-only | ⚪ |
| **Неотслеживаемые git файлы** | bin/, calendar/, plugins/, skills/*, workspace/health/deploy/, first_analysis.py | ⚪ Разложить по коммитам |

---

## 12. Что забыто / заброшено

### 12.1 Незавершённые задачи из дневников

1. **CalDAV конфиги** (TODO с 06.09) — vdirsyncer/khal установлены, но не настроены
2. **Composio smoke-test** (12.09) — permissions не проверены
3. **Oura таймеры** — установлены, но не включены владельцем
4. **Рестарт r2d2-hub** — нужен для применения `.env` с `OPENCLAW_AGENT_ID=chat`
5. **Миграция secrets на SecretRef** — 15 plaintext findings, рекомендована ротация OpenAI-ключа
6. **Git cleanup** — неотслеживаемые файлы не разложены по коммитам

### 12.2 Заброшенные компоненты

- **Mini App** — полностью мёртв, заменён сайтом hub.gbkz.uk
- **Pollinations.ai** — никогда не был настроен на этом сервере (путаница с Gemini Flash Image Preview)
- **Astra 6 (gpt-6-astra)** — недоступна без Codex кредитов, хозяин сказал «забываем»
- **Google provider** — отключён по правилу

### 12.3 Бэкапы и артефакты

- `/root/_trash/ideal-20260911/` — бэкапы аудита (можно почистить после подтверждения)
- `openclaw-gateway.service.bak` — артефакт обновления
- Временные скрипты `_install_timers.py`, `_fix_hub_env.py` уже убраны в _trash

---

## 13. Хаб (r2d2-hub)

- **Репо:** `/root/atlas-green-pearl-dawn`
- **Сервис:** r2d2-hub.service → :8091
- **URL:** https://hub.gbkz.uk
- **Probes:** /healthz, /readyz
- **Env:** `/root/atlas-green-pearl-dawn/.env`
  - `OPENCLAW_AGENT_ID=hub` (⚠️ должен быть `chat`)
  - `OPENCLAW_GATEWAY_URL=http://127.0.0.1:18789`
  - `OPENCLAW_MODEL=openclaw/hub`
- **Watchdog скрипты:** hub-backup.sh (flock), disk-check.sh
- **Код хаба не трогать** без прямого ТЗ хозяина с явным списком файлов

---

## 14. Рекомендации (приоритетный список)

### 🔴 Срочно (блокирует функциональность)

1. **Починить Telegram бота** — `/codex stop` + `/codex resume` или рестарт gateway
2. **Разобрать dead-letter queue** — 3 входящих telegram сообщения потеряны

### 🟡 Важно (улучшает надёжность)

3. **Включить Oura таймеры** — `systemctl --user daemon-reload && systemctl --user enable --now health-morning.timer health-weekly.timer health-monthly.timer`
4. **Рестарт r2d2-hub** — применить `.env` с правильным `OPENCLAW_AGENT_ID=chat`
5. **Завершить Composio smoke-test** — проверить permissions
6. **Миграция secrets на SecretRef** — начать с `channels.*`, `openai` последним
7. **Создать CalDAV конфиги** — vdirsyncer/khal уже установлены

### ⚪ Можно сделать когда-нибудь

8. Удалить мёртвые юниты (miniapp.service, openclaw-gateway.service.bak)
9. Разложить неотслеживаемые git файлы по коммитам
10. Почистить `/root/_trash/`
11. Отключить legacy Browser Relay auth
12. Добавить Jina/Brave ключ в env gateway

### 💡 Архитектурные улучшения

13. **Image generation:** создать skill `openrouter-images` для доступа ко всем 53 моделям OpenRouter Images API (Seedream, FLUX, Recraft и др.)
14. **Monitoring:** настроить алерты на dead-letter queue и stale sessions
15. **Secrets rotation:** регулярная ротация API-ключей (особенно OpenAI, который побывал в plaintext)

---

## 15. История версий и обновлений

| Дата | Версия | Событие |
|---|---|---|
| 27.08 | 2026.7.1-2 | Первоначальная настройка, ребут, ядро 6.8.0-138 |
| 06.09 | 2026.9.1 → 2026.9.2 | Обновление (первая попытка упала, вторая прошла) |
| 10.09 | 2026.9.2 | Exec починен, image_generate протестирован |
| 11.09 | 2026.9.4 | Обновление, Oura sync 18 коллекций, аудит сервера |
| 12.09 | 2026.9.4 | Composio установлен, hub scripts fixed |
| 14.09 | 2026.9.4 | Текущая сессия, модель relaymodels/kimi-k2.7-code |

---

*Документ сгенерирован агентом Crestodian (main) на основе памяти, конфигов и системного состояния.*
