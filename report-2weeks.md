# Расширенный отчёт: Изменения, правки, ошибки и проблемы (01.09–14.09.2026)

> **Сервер:** hiplet-112102 (VPS Франкфурт DE)
> **OpenClaw:** 2026.7.1 → 2026.9.4
> **Период:** 01.09.2026 – 14.09.2026
> **Составил:** Crestodian (main agent)
> **Дата:** 2026-09-14 12:30 UTC

---

## Содержание

1. Хронология обновлений OpenClaw
2. Изменения конфигурации
3. Новые интеграции и провайдеры
4. Ошибки и инциденты
5. Проблемы безопасности
6. Изменения в памяти и архитектуре
7. Незавершённые задачи и хвосты
8. Метрики и статистика
9. Рекомендации на следующий период

---

## 1. Хронология обновлений OpenClaw

| Дата | Версия | Способ | Результат | Примечания |
|------|--------|--------|-----------|------------|
| 27.08 | 2026.7.1-2 | — | Базовая установка | Ядро 6.8.0-138, ребут |
| 06.09 | 2026.9.1→9.2 | openclaw update | ⚠️ Первая попытка упала. Вторая прошла. | Появился skill control-ui |
| 11.09 | 2026.9.2→9.4 | openclaw update | ✅ Успешно | Коммит 3a9d69d. Oura sync 18 коллекций |
| 14.09 | 2026.9.4 | — | Текущая | Phantom failed update исправлен на succeeded |

### Детали обновлений

**06.09 — Обновление 2026.9.1 → 2026.9.2:**
- Первая попытка: post-core-update-failed, runtime-verification-failed
- Вторая попытка: global update + doctor, gateway перезапущен
- Новые skills: control-ui
- Автообновления: deepseek plugin → 2026.9.2, expedia-openclaw → 1.0.4
- Не обновлены: parallel-plugin, searxng-plugin (остались 2026.9.1)
- Установлены: diffs 2026.9.2, tokenjuice 2026.9.2, aviasales-flights skill

**11.09 — Обновление до 2026.9.4:**
- Успешное обновление, коммит 3a9d69d
- Oura sync расширен на все 18 коллекций API
- Первая полная выкачка: 103 544 строки за 30 дней, база 24 MB
- Аудит сервера выполнен (DeepSeek executor, не Codex)

---

## 2. Изменения конфигурации

### 2.1 Модельные провайдеры

| Провайдер | Добавлен/Изменён | Статус | Примечания |
|-----------|------------------|--------|------------|
| deepseek | Базовый | ✅ Работает | v4-flash, v4-pro, chat, reasoner, flash (V4.1) |
| openrouter | Базовый | ✅ Работает | auto, qwen-image-3-pro, glm-5.3-flash |
| relaymodels | Новый (12.09) | ✅ Работает | gpt-5.6-luna, deepseek-v4-flash/pro, kimi-k2.7-code, qwen3.8-max |
| openai | Новый (11.09) | ⚠️ Частично | Astra недоступна (model_not_found, 47 отказов) |
| jina | Базовый | ✅ Embeddings | jina-embeddings-v3 |

### 2.2 Дефолтные модели

| Период | Default Chat | Image Primary | Image Fallback |
|--------|-------------|---------------|----------------|
| 01–10.09 | deepseek/deepseek-v4-flash | — | — |
| 11–14.09 | deepseek/deepseek-v4-pro | openrouter/openai/gpt-5.4-image-2 | openrouter/google/gemini-3.1-flash-image-preview |

### 2.3 Model Policy

```
agents.defaults.modelPolicy.allow:
  - deepseek/deepseek-v4-flash
  - deepseek/deepseek-v4-pro
  - deepseek/deepseek-v4-flash-vision-exp
  - deepseek/deepseek-flash
  - deepseek/deepseek-chat
  - relaymodels/*      (добавлено 12.09)
  - openrouter/*       (добавлено 11.09)
```

### 2.4 Плагины

| Плагин | 01.09 | 14.09 | Изменения |
|--------|-------|-------|-----------|
| codex | enabled | disabled (14.09) | Отключён по рекомендации стабилизации |
| composio | — | enabled (12.09) | Hook-only mode |
| openai | — | enabled (11.09) | personality:on |
| google | enabled | disabled | По правилу |
| perplexity | enabled | disabled | По правилу |
| diffs | — | enabled (06.09) | 2026.9.2 |
| tokenjuice | — | enabled (06.09) | 2026.9.2 |
| browser | enabled | enabled | Legacy Relay auth warning |
| memory-core | enabled | enabled | Dreaming cron: 0 3 * * * |

### 2.5 Exec-политика

| Параметр | Значение |
|----------|----------|
| mode | auto |
| security | allowlist |
| ask | off |
| askFallback | deny |
| Allowlist (01.09) | ls, cat, head, tail, df, journalctl, date, uname, free, zramctl, mkdir, mv, tar, gpg, git, ss, curl, openclaw |
| Allowlist (14.09) | + python3, grep, find, sqlite3, /usr/bin/node, /usr/bin/npm, composio CLI, aviasales operator, health scripts |

### 2.6 Агенты

| Агент | 01.09 | 14.09 | Изменения |
|-------|-------|-------|-----------|
| main | active | active (57 sessions) | — |
| chat | active | active (17 sessions) | Restricted profile |
| groups | active | active (1 session) | groupAllowFrom сужен |
| health | — | active (1 session) | Добавлен для Oura |
| hub | active | удалён (11.09) | По ТЗ Дмитрия |
| openclaw | — | exists (0 sessions) | — |

### 2.7 Каналы

| Канал | Статус | Примечания |
|-------|--------|------------|
| Telegram | ON / OK | Токен sha256:4c220679, allowlist: 1916536646, 8335493342 |
| WebChat | ON | Dashboard :18789, external ui.gbkz.uk |

---

## 3. Новые интеграции и провайдеры

### 3.1 Oura Ring (11.09)

**Статус:** ✅ Полностью интегрирована

- OAuth2 callback сервис на :8092
- Sync скрипт: workspace/health/scripts/oura_sync.py
- База данных: workspace/health/data/oura.db (SQLite, таблица oura_raw)
- 18 коллекций API: heartrate, sleep, workout, daily_activity, readiness, resilience, spo2, stress, vO2_max, cardiovascular_age, sleep_time, session, tag, enhanced_tag, ring_configuration, personal_info, rest_mode_period
- Первая выкачка: 103 544 строки за 30 дней (2026-08-12..09-11), errors={}
- Analytics v2.1: workspace/health/scripts/analytics.py
- Таймеры: morning/weekly/monthly установлены, но НЕ включены (TODO)

**Ошибки при интеграции:**
- Heartrate endpoint давал 400 → исправлен (неправильный путь)
- vO2_max: большая O в названии (раньше 404)
- /stats требовал рестарта сервиса после правки

### 3.2 RelayModels (12.09)

**Статус:** ✅ Работает

- Base URL: api.relaymodels.com/v1
- Модели: gpt-5.6-luna, deepseek-v4-flash, deepseek-v4-pro, kimi-k2.7-code, qwen3.8-max
- Используется как текущая модель сессии (relaymodels/kimi-k2.7-code)

### 3.3 OpenAI Provider (11.09)

**Статус:** ⚠️ Частично работает

- Ключ Дмитрия добавлен через SecretRef
- Проект: proj_VaCPWc9LX5oP2QCejHBHFNK3
- Модели настроены: gpt-5.6, gpt-5.5, gpt-5.6-sol/luna/terra, gpt-6-astra
- Проблема: gpt-6-astra возвращает model_not_found (47 отказов)
- Хозяин: «про Codex забываем» → Astra закрыта

### 3.4 Composio (12.09)

**Статус:** ⚠️ Установлен, smoke-test не завершён

- Плагин: @composio/composio@0.1.0
- CLI: /root/.composio/cli/composio (@composio/cli@0.4.1)
- Авторизация: managed auth/OAuth
- Permissions + smoke-test: не завершены

### 3.5 CalDAV Calendar (06.09)

**Статус:** ⚠️ Bins установлены, конфиги не созданы

- Skill: caldav-calendar (vdirsyncer + khal)
- apt install vdirsyncer khal выполнен ✅
- Конфиги vdirsyncer/khal: НЕ созданы (TODO с 06.09)

### 3.6 Aviasales/Travelpayouts (06.09)

**Статус:** ⚠️ Skill установлен, токен требует проверки

- TRAVELPAYOUTS_TOKEN засветился в чате → рекомендована ротация
- Запись .env через инструменты агента провалилась
- Финальная команда выдана владельцу, результат не проверен

### 3.7 Claude Proxy (03.09)

**Статус:** ❌ Не работает

- Инференс 503 на всех моделях (бэкенд посредника лежит)
- Прямого Anthropic-ключа нет

---

## 4. Ошибки и инциденты

### 4.1 Критические

| Дата | Инцидент | Причина | Resolution |
|------|----------|---------|------------|
| 06.09 | Update первая попытка упала | post-core-update-failed | Вторая попытка прошла |
| 11.09 | Telegram бот молчал | Codex session policy handoff failed | Рестарт или /codex stop+resume |
| 11.09 | OpenAI Astra model_not_found | Нет доступа к gpt-6-astra | Закрыто |
| 14.09 | Exec полностью заблокирован | SQLite malformed после ручной правки | Очищены битые записи, рестарт |
| 14.09 | Phantom failed update | status=failed, reason=null | Исправлен на succeeded |

### 4.2 Средние

| Дата | Проблема | Статус |
|------|----------|--------|
| 06.09 | TRAVELPAYOUTS_TOKEN засветился | Ротация не выполнена |
| 06.09 | .env запись через агента битая | Урок: только команды владельца |
| 10.09 | Exec cannot bind pipes/redirects | Известное ограничение |
| 11.09 | Dead-letter queue: 3 inbound telegram | Oldest 26 дней |
| 11.09 | Stale Codex/OpenAI session state | Требует очистки |
| 12.09 | RELAYMODELS_API_KEY missing env var | Warning |
| 14.09 | Memory system not found warning | Может уйти после рестарта |

### 4.3 Низкие

| Дата | Проблема | Статус |
|------|----------|--------|
| 03.09 | Claude proxy 503 | Не наш контроль |
| 06.09 | parallel/searxng не обновлены | TODO |
| 11.09 | miniapp.service мёртвый | Можно удалить |
| 11.09 | telegram-user-svc молчит с 27.08 | Отдельная задача |
| 11.09 | .env хаба AGENT_ID=hub | Исправлено на chat |
| 14.09 | Legacy Browser Relay auth | Warning |

---

## 5. Проблемы безопасности

### 5.1 Secrets Audit

- 15 plaintext findings в openclaw.json
- Unresolved: 0
- Миграция на SecretRef: НЕ выполнена

### 5.2 Утечки токенов

| Дата | Токен | Обстоятельства | Действие |
|------|-------|----------------|----------|
| 03.09 | sk-myapi_* (Claude proxy) | В переписке | Не ротирован |
| 06.09 | TRAVELPAYOUTS_TOKEN | Засветился в чате | Ротация не выполнена |

### 5.3 Exec-политика

- Headless: всё вне allowlist = deny
- Auto-review режет rm -rf в /root
- 14.09: Прямая запись в SQLite сломала exec → восстановлен

### 5.4 Access Control

- Owner: 1916536646 → main agent
- Managed: 8335493342 → chat agent (restricted)
- Groups: groupAllowFrom = [1916536646]
- Новые пользователи: restricted по умолчанию

---

## 6. Изменения в памяти и архитектуре

### 6.1 Структура памяти

| Компонент | 01.09 | 14.09 | Изменения |
|-----------|-------|-------|-----------|
| MEMORY.md | exists | exists | Project-scoping маркер 14.09 |
| USER.md | exists | exists | Маркер + стиль ужесточён |
| SOUL.md | exists | exists | Маркер + «Память (жёсткое правило)» |
| AGENTS.md | exists | exists | Маркер 14.09 |
| IDENTITY.md | exists | exists | Маркер 14.09 |
| Дневники | 03,04,06,10,11,12 | + 14-stabilization-report | 7 файлов |
| Dreaming | dreaming/{deep,light,rem} | Вынесено в persistent dir | Symlink 14.09 |
| Project-scoping | частичный | все 14 файлов | Маркеры 14.09 |

### 6.2 Persistent Memory (14.09)

- Память вынесена: /root/openclaw-state/memory/
- Symlink: /root/openclaw/memory → /root/openclaw-state/memory
- Защита от амнезии при обновлениях
- .gitignore: /memory/*.md исключены

### 6.3 Директива памяти (14.09)

Добавлена в SOUL.md:
> Перед ответом на любой вопрос о прошлых событиях — ТЫ ОБЯЗАН использовать memory_search.

---

## 7. Незавершённые задачи и хвосты

### 7.1 Активные TODO

| # | Задача | С даты | Приоритет |
|---|--------|--------|-----------|
| 1 | Включить Oura таймеры | 11.09 | 🟡 Высокий |
| 2 | Composio smoke-test | 12.09 | 🟡 Высокий |
| 3 | CalDAV конфиги | 06.09 | 🟡 Средний |
| 4 | Миграция secrets на SecretRef | 06.09 | 🟡 Средний |
| 5 | Ротация TRAVELPAYOUTS_TOKEN | 06.09 | 🟡 Средний |
| 6 | parallel/searxng plugins update | 06.09 | ⚪ Низкий |
| 7 | Удалить miniapp.service | 11.09 | ⚪ Низкий |
| 8 | Разобрать dead-letter queue | 11.09 | ⚪ Низкий |

### 7.2 Заброшенные компоненты

- Mini App — мёртв, заменён hub.gbkz.uk
- Pollinations.ai — никогда не был настроен
- Astra 6 (gpt-6-astra) — закрыта
- Claude proxy — 503, не наш контроль
- Google provider — отключён

---

## 8. Метрики и статистика

### 8.1 Сессии и агенты

| Метрика | Значение |
|---------|----------|
| Всего агентов | 5 |
| Всего сессий | 76 |
| Main sessions | 57 |
| Chat sessions | 17 |

### 8.2 Oura данные

| Метрика | Значение |
|---------|----------|
| Строк в oura_raw | 103 544 |
| Размер БД | 24 MB |
| Коллекций API | 18 |
| Errors | {} (пусто) |

### 8.3 Delivery Queue

| Тип | Количество | Статус |
|-----|-----------|--------|
| Active/pending | 0 | — |
| Total entries | 49 | Все archived |

### 8.4 Бэкапы (14.09)

| Артефакт | Размер | Тип |
|----------|--------|-----|
| pre-fix-workspace-20260914.tgz | 371 MB | Workspace tar |
| pre-fix-state-20260914.tgz | 631 MB | State tar |
| pre-fix-db-consistent-20260914/ | 646 MB | SQLite backup API |

---

## 9. Рекомендации на следующий период

### 🔴 Срочно

1. Включить Oura таймеры
2. Composio smoke-test
3. Ротация OpenAI-ключа

### 🟡 Важно

4. CalDAV конфиги
5. Миграция secrets на SecretRef
6. Проверить TRAVELPAYOUTS_TOKEN
7. parallel/searxng plugins update

### ⚪ Можно позже

8. Удалить мёртвые юниты
9. Разобрать dead-letter queue
10. Отключить legacy Browser Relay auth
11. Расширить image_generate каталог

---

## Приложение: Хронология сессий по дням

| Дата | Ключевые события |
|------|-----------------|
| 03.09 | Аудит системы, хаб обновлён, Claude proxy тест (503) |
| 04.09 | Telegram-first access control, bot-access-operator rewrite |
| 06.09 | Обновление 9.1→9.2, parallel-free поиск, aviasales skill, TRAVELPAYOUTS сага |
| 10.09 | Exec починен, image_generate протестирован |
| 11.09 | Oura OAuth2 + 18 коллекций, hub удалён, OpenAI provider, update 9.4 |
| 12.09 | RelayModels, Codex/Astra закрыты, Composio installed |
| 13.09 | (нет дневника) |
| 14.09 | Стабилизация: бэкапы, Codex off, phantom fix, persistent memory, exec restore |

---

*Документ сгенерирован агентом Crestodian (main).*
*Формат: Markdown (.md). Для MDF использовать pandoc.*