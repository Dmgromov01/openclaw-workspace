# Доказательный аудит OpenClaw-агента (Crestodian) — 24.08.2026, v2

Principal-level review. Все выводы помечены статусом доказательности:
**CONFIRMED** (артефакт проверен) / **LIKELY** / **UNVERIFIED** / **N/A**.

---

## A. Executive Summary

1. **Система рабочая, но в git-истории лежит активный секрет** — это P0-инцидент, требующий ротации, а не просто удаления файлов.
2. **Файрвол выключен** (ufw inactive), хотя MEMORY.md утверждает обратное — несостыковка документации и реальности.
3. **miniapp доступен из интернета** (0.0.0.0:8080, внешний curl → 200) без TLS; auth есть на уровне приложения (401 без токена), но транспорт открытый.
4. **Чувствительные БД в git**: miniapp.db (password_hash, 25 сессионных токенов, audit_log), ai-memory.db (схема с embedding-колонкой), data/app.db — в репозитории.
5. **.venv (343MB, 5615 файлов) закоммичен** — репо раздут до ~92MB.
6. Плагины (tg-user-tools, jina-tools) делают fetch **без таймаутов/AbortSignal** — зависший вызов вешает агента.
7. Есть дубли (flight_watch + flight_api), мёртвый код (icloud_calendar, orchestrator), устаревшие доки (healthcheck, MEMORY.md).
8. Позитив: секреты прод-конфига вне git, credentials 600, плагины на официальном SDK, healthcheck + cron есть, Google Calendar OAuth корректен.
9. **Сначала P0 (ротация токена, закрыть порт, вычистить git), потом P1 (таймауты, дубли), потом P2/P3.**
10. Чего не хватает для полного аудита: метрики токенов/latency (нет telemetry), содержимое .clawpatch, история промптов.

---

## B. Evidence Map

| ID | Finding | Status | Evidence | Component | Severity |
|---|---|---|---|---|---|
| E1 | Активный bot token в git-истории | CONFIRMED | `git log --all -p` → `REDACTED-TELEGRAM-TOKEN` (совпадает с openclaw.json) + старый `7963335559:AAFA...` | Git history / Telegram | CRITICAL |
| E2 | miniapp.db, ai-memory.db, data/app.db в git | CONFIRMED | `git ls-files | grep .db`; miniapp.db: users(password_hash), sessions(25), audit_log(27) | Git / Storage | CRITICAL |
| E3 | .venv (5615 файлов, 343MB) в git | CONFIRMED | `git ls-files | grep -c '^.venv/'` = 5615; duckdb.so 60MB | Git / Dependencies | HIGH |
| E4 | ufw INACTIVE | CONFIRMED | `/usr/sbin/ufw status` → `Status: inactive` | Firewall | CRITICAL |
| E5 | miniapp 0.0.0.0:8080 доступен снаружи | CONFIRMED | `ss -tlnp` → 0.0.0.0:8080; `curl http://138.124.180.178:8080/` → 200 | miniapp/Network | CRITICAL |
| E6 | Плагины без таймаутов | CONFIRMED | tg-user-tools/index.js: `fetch(BASE+...)` без AbortSignal; jina-core.js: jinaPost/jinaGet без AbortSignal | Plugins | HIGH |
| E7 | Дубль мониторинга цен | CONFIRMED | crontab: flight_watch.py 6:00/18:00 + flight_api.py 6:10/18:10, оба шлют в TG | Cron | MEDIUM |
| E8 | Мёртвый код | CONFIRMED | icloud_calendar.py (327 строк, календарь=Google); orchestrator.py (заглушка `_collect_news`); backup-crontab ссылается на несуществующие services/assistant_bot/* | Scripts | MEDIUM |
| E9 | Застрявшая delivery | CONFIRMED | journalctl: `delivery a4fc1e2a... state is send_attempt_started; refusing blind replay... 0 recovered, 1 failed` | Gateway/Queue | MEDIUM |
| E10 | healthcheck.sh устарел | CONFIRMED | Пишет «telegram-user-svc: не systemd», а `systemctl` показывает active unit telegram-user-svc.service | Healthcheck | LOW |
| E11 | Два venv (343MB + 403MB) | CONFIRMED | du -sh: .venv 343M, venv 403M | Dependencies | LOW |
| E12 | memorySearch платный | CONFIRMED | openclaw.json: provider=openai-compatible, model=openai/text-embedding-3-small via OpenRouter (платно); Jina бесплатен в квоте | Memory | MEDIUM |
| E13 | bot_sender.py парсит openclaw.json руками | CONFIRMED | bot_sender.py `_get_token()`: читает accounts.default.botToken / botToken / файл-ссылку | Scripts | MEDIUM |
| E14 | reportlab в system python | CONFIRMED | `pip list` → reportlab 5.0.1 (поставлен мной сегодня через --break-system-packages) | Runtime | LOW |
| E15 | certbot.service failed | CONFIRMED | `systemctl --failed` → certbot.service failed (но nginx/TLS работает, сертификат до 17.11.2026) | Infra | LOW |
| E16 | miniapp API auth работает | CONFIRMED | curl /api/calendar без токена → 401; initData HMAC + password_hash в SQLite | miniapp | INFO |
| E17 | Другие API-ключи в истории git | CONFIRMED-отрицательно | Паттерны sk-/sk-or-/ghp_/AIza/AQ. в diff — не найдены (только bot token'ы) | Git history | INFO |
| E18 | .env никогда не был в git | CONFIRMED | `git log --all --diff-filter=A -- .env` → пусто | Git history | INFO |
| E19 | ai-memory.db содержит embeddings | LIKELY | Схема: колонка `embedding`, таблица memories (0 строк сейчас) | Storage | LOW |
| E20 | Токен-метрики/latency отсутствуют | CONFIRMED | Нет telemetry в конфиге; логи только текстовые | Observability | MEDIUM |

---

## C. Scorecard

| Направление | Score | Rationale | Risk |
|---|---|---|---|
| Security | 4/10 | Активный секрет в git-истории, ufw off, публичный 8080; но credentials 600, .env вне git | CRITICAL |
| Architecture | 6/10 | Ядро чистое, периферия разрознена (4 пути отправки TG, скрипты без общего слоя) | MEDIUM |
| Plugin isolation | 5/10 | SDK-контракты верны, но нет таймаутов, нет per-plugin permissions, общий FS | MEDIUM |
| Code quality | 5/10 | Мёртвый код, дубли, хрупкий парсинг конфига | MEDIUM |
| Reliability | 5/10 | Нет таймаутов/circuit breaker; застрявшая delivery; cron без locking | HIGH |
| Observability | 3/10 | Нет метрик токенов/latency, логи без ротации, healthcheck устарел | MEDIUM |
| Performance | 6/10 | RAG переиндексация при любом изменении; npx-серверы на старте | MEDIUM |
| Token efficiency | 5/10 | Платный embeddings, нет кэша digest, нет routing | MEDIUM |
| Maintainability | 4/10 | Два venv, устаревшие доки, 15 бэкапов конфига | MEDIUM |
| Deployment maturity | 5/10 | systemd-юниты есть, но ufw off, certbot failed, нет CI | MEDIUM |

---

## D. P0: Incident Response Plan

### D1. Активный Telegram bot token в git-истории (E1)

- **Finding**: `REDACTED-TELEGRAM-TOKEN` — текущий токен бота @Dmbotmy_bot — присутствует в истории git (коммиты 2e2e689, 32d6717 и др.). Репо приватное, но история нестираема.
- **Immediate containment (1–4 часа)**:
  1. **Ротация токена**: @BotFather → /revoke → новый токен → обновить в `/root/.openclaw/openclaw.json` + `/root/.openclaw/.env` (TELEGRAM_BOT_TOKEN) → `systemctl --user restart openclaw-gateway.service`. Старый токен умирает мгновенно.
  2. Верифицировать: `curl api.telegram.org/bot<OLD>/getMe` → 401 после ротации.
- **Secret rotation**: токен бота (обязательно); проверить miniapp HMAC-секрет (строится из bot token — после ротации обновить, иначе initData-верификация сломается).
- **Exposure cleanup**:
  1. `git rm --cached` для *.db и .venv (см. D2/D3).
  2. История: репо приватный; полный purge (git filter-repo) — только если репо покидал машину (был ли форк/клон? — UNVERIFIED). Минимально: ротация токена делает утечку бесполезной; purge — желателен, но не блокер.
- **Validation**: `git log --all -p | grep <token>` → пусто после purge (или токен неактуален); бот отвечает новым токеном.
- **Backout**: держать старый токен записанным в /root/.openclaw/credentials/legacy-tokens.txt до полной уверенности; при сбое нового — вернуть старый (до истечения).
- **Risk if delayed**: любой с доступом к репо (или утёкшему бэкапу) может управлять ботом: читать/писать от имени бота, рассылать спам.

### D2. Чувствительные БД в git (E2)

- **Containment**: `git rm --cached miniapp/miniapp.db ai-memory.db data/app.db` → commit → push. Файлы остаются на диске, уходят из репо.
- **Data invalidation**: miniapp — сбросить таблицу sessions (25 токенов) → пользователи перелогинятся; password_hash — сменить пароль владельца.
- **Git history**: purge через filter-repo (репо приватный — приоритет средний, но желательно).
- **Validation**: `git ls-files | grep .db` → пусто; `git log --all --oneline -- miniapp.db` → пусто после purge.
- **Backout**: бэкап БД перед сбросом сессий в /root/.openclaw/backups/.

### D3. Публичный miniapp + ufw off (E4, E5)

- **Containment (1 час)**:
  1. Включить ufw: `ufw allow 22/tcp; ufw allow 80,443/tcp; ufw allow from 100.64.0.0/10 (tailnet); ufw default deny incoming; ufw enable`.
  2. Перевести miniapp на loopback: правка `miniapp/server.py` → `("127.0.0.1", port)` → `systemctl --user restart miniapp.service`.
  3. Если нужен доступ снаружи — nginx reverse proxy с TLS (как gbkz.uk), иначе только tailnet/локально.
- **Validation**: `ufw status` → active; `ss -tlnp` → 8080 на 127.0.0.1; `curl http://138.124.180.178:8080/` → timeout/refused.
- **Backout**: вернуть bind 0.0.0.0, ufw disable (не рекомендуется).

---

## E. P1: Reliability Hardening

### E1-P. Таймауты в плагинах (E6)

- **Failure mode**: зависший HTTP-вызов (Jina/telegram-user-svc не отвечает) → tool call висит бесконечно → агент не отвечает, токены горят.
- **Trigger**: сетевой сбой, перегрузка провайдера, полузакрытое соединение.
- **Current behaviour**: fetch без AbortSignal — висит до таймаута ОС (минуты).
- **Desired**: таймаут 10–15s на connect+read; ошибка → retry с backoff (для идемпотентных GET), затем понятная ошибка агенту.
- **Implementation**: единый helper `fetchJson(url, {timeout})` с `AbortSignal.timeout()`; в jina-core уже есть retry на 429 — добавить timeout на сам fetch; в tg-user-tools — обернуть `call()`.
- **Test**: mock-сервер, который не отвечает 30s → tool падает за ~10s с ошибкой «timeout», агент продолжает.
- **Observability**: логировать duration/status каждого tool-call.
- **Rollback**: правка одного файла плагина.

### E2-P. Дубли cron (E7)

- **Failure mode**: два скрипта шлют противоречивые/дублирующие уведомления о ценах.
- **Fix**: оставить flight_api.py (API надёжнее парсинга HTML), flight_watch.py удалить/перевести в fallback; единый state-файл.
- **Test**: один запуск cron → одно уведомление.

### E3-P. Застрявшая delivery (E9)

- **Failure mode**: сообщение a4fc1e2a никогда не доставится; recovery блокирует replay.
- **Fix**: разобрать вручную: найти запись в delivery-очереди OpenClaw, либо сбросить состояние записи (после сверки с адаптером), либо удалить как устаревшую.
- **Test**: после фикса recovery: 0 pending / 0 failed.

### E4-P. Остальное P1

- cron locking (flock) против одновременных запусков digest/flight (сейчас cron гарантирует, но ручной запуск может пересечься).
- Ротация логов: logrotate для healthcheck.log, flight_*.log, .clawpatch/weekly.log.
- healthcheck.sh: актуализировать (svc — systemd unit), добавить проверку git-чистоты и ufw.

---

## F. P2/P3: Architecture and Optimization

### Плагины
- **jina-tools**: кэш 10MB с原文 фрагментами — chmod 600 + очистка; переиндексация только по изменению state (уже есть) + ручной инвалидатор; добавить `topN` cap (сейчас без лимита).
- **Единый HTTP-слой** для плагинов (timeout/retry/redaction) — убрать дублирование fetch-логики.

### Runtime/код
- Удалить мёртвый код: icloud_calendar.py, orchestrator.py, backup-crontab-20260820.txt, tmp/cbc_en.py (или перенести в _trash_).
- bot_sender.py: читать токен из credentials-файла, не парсить openclaw.json.
- Один venv + requirements.txt (pip freeze), reportlab перенести в venv.

### Storage
- *.db и .venv — в .gitignore (`*.db`, `.venv/`); `git rm --cached`.
- Бэкапы БД: cron с ротацией (7 дней) в /root/.openclaw/backups.

### Prompt/context/tokens
- **memorySearch → Jina embeddings** (бесплатно в квоте 10M) вместо платного OpenRouter text-embedding-3-small: экономия $/мес.
- **digest**: кэшировать посты по времени/ETag; суммаризировать только посты, прошедшие фильтр (не все 3/канал).
- **Токен-бюджет на tool-calls**: cap на размер ответа инструмента (jina_search уже режет 15K — ок), cap на число tool-calls в workflow.

### Model routing
- Router перед дорогой моделью: простые задачи — flash, сложные — pro (fallback уже есть deepseek-v4-pro; добавить явный routing по типу задачи).

### Background jobs
- Один cron-файл + flock; логи с ротацией; алерт при failure (уже есть healthcheck — расширить на новые сервисы).

### Deployment
- ufw-политика как код (скрипт), nginx-конфиг в git, certbot-юнит починить (или удалить failed unit, timer работает).

---

## G. Token and Cost Baseline (telemetry plan)

Метрик сейчас нет — минимальный план:

1. **Логировать**: каждый tool-call (tool, duration_ms, status, tokens_used), каждый LLM-call (model, input/output tokens, latency, cache_hit).
2. **Метрики**: cost/day по провайдеру, tokens/task (задача = сообщение пользователя → финальный ответ), P50/P95 latency, retry/error rate, cache hit rate.
3. **Сегментация**: по workflow (дайджест / RAG / image / chat), по провайдеру (deepseek/openrouter/google/jina), по модели.
4. **Baseline**: 7 дней сбора → cost/task, tokens/task, latency P95.
5. **Эффект**: замерять до/после каждого изменения (memorySearch→Jina, кэш digest, routing).

---

## H. Target Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                 OpenClaw Gateway (systemd)                    │
│   Agent Core: orchestration, context budget, tool policy      │
├───────────┬──────────────┬─────────────┬──────────────────────┤
│ Tool GW   │ Plugin Rtm   │ Memory      │ Channels             │
│ timeout/  │ manifest+    │ hybrid      │ telegram (nginx TLS) │
│ retry/    │ contract+    │ search      │                      │
│ redaction │ lifecycle    │ Jina RAG    │                      │
├───────────┴──────────────┴─────────────┴──────────────────────┤
│ Isolated services (systemd):                                  │
│  miniapp (127.0.0.1, nginx TLS) · telegram-user-svc (8765)    │
├──────────────────────────────────────────────────────────────┤
│ Storage: credentials/ (600) · cache/ (600) · backups/ · *.db   │
│   (вне git, ротация, retention)                               │
├──────────────────────────────────────────────────────────────┤
│ Guardrails: ufw (default deny) · tool timeouts · token caps   │
│  · per-plugin permissions · log redaction · audit             │
└──────────────────────────────────────────────────────────────┘
```

- **Agent Core** не ходит напрямую в сеть/БД/шелл — только через Tool Gateway.
- **Tool Gateway**: единый слой timeout/retry/redaction/correlation-id.
- **Plugin Runtime**: manifest → validate → init → healthcheck → execute → unload; изоляция FS по workspace.
- **Queue/Outbox**: для доставки (решить проблему a4fc1e2a); digest — не нужна очередь, малый объём.
- **Secrets**: только credentials/ (600), никогда в git/logs; ротация по расписанию.
- **Observability**: структурированные логи + метрики токенов/latency.
- **Deployment**: ufw как код, nginx-конфиги в git, единый venv + lockfile.

---

## I. Implementation Roadmap

| Период | Задачи | Результат | Метрика успеха |
|---|---|---|---|
| Первые 4 часа | P0: ротация bot token; ufw enable; miniapp → 127.0.0.1; git rm --cached *.db/.venv | Риск утечки остановлен | Старый токен 401; ufw active; 8080 закрыт снаружи |
| 1–3 дня | P0: сброс сессий miniapp, purge git history (filter-repo), актуализация healthcheck; P1: таймауты в плагинах | Система безопаснее, наблюдаема | git ls-files без .db/.venv; tool-call падает за 10s |
| 1–2 недели | P1: разбор delivery, дубли cron, ротация логов, certbot | Меньше сбоев и дублей | pending=0; одно уведомление на запуск; логи с ротацией |
| 2–6 недель | P2/P3: memorySearch→Jina, кэш digest, единый venv+lockfile, routing, telemetry | Ниже стоимость и задержка | cost/task −20–40%; tokens/task −20%; P95 latency −30% |

---

## J. Final Verdict

1. **P0 немедленно**: активный bot token в git-истории + ufw off + публичный 8080 — это три реальных инцидента, не гипотезы (CONFIRMED, артефакты выше).
2. **Ротация токена обязательна** — `git rm --cached` не лечит утечку из истории.
3. **Плагины без таймаутов** — самый дешёвый и важный P1-фикс (10 минут, один helper).
4. **Мёртвый код и дубли** — не «полировка», а источник путаницы и будущих ошибок (healthcheck уже врёт про systemd).
5. **memorySearch на OpenRouter — лишние деньги** при наличии бесплатной Jina-квоты: переключить.
6. **Документация отстала от реальности** (MEMORY.md про ufw, healthcheck про svc) — обновить после фиксов, иначе следующий аудит наступит на те же грабли.
7. **Telemetry отсутствует** — без метрик токенов/latency любые «оптимизации» — гадание; начать сбор до P3.
8. **Архитектура ядра хорошая** — проблемы в периферии (скрипты, плагины, cron), не в OpenClaw core.
9. **Порядок**: P0 сегодня → P1 на этой неделе → P2/P3 через 2–6 недель; не менять архитектуру, пока не закрыты security/reliability.
10. **Ожидаемый результат после P0/P1**: ни одного секрета в git, закрытый периметр, tool-calls с таймаутами, один источник правды по ценам, работающий healthcheck.
