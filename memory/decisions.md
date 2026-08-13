# Decisions — журнал ключевых архитектурных решений

## 12.08 — Домен и вход
- gbkz.uk (Cloudflare → nginx → OpenClaw 18789) — основной домен. dmkz.org заброшен (Timeweb, РФ-регистратор, блок смены NS).
- auth.mode = token (не password); iPhone подключается через setup code по wss://gbkz.uk:443.
- Урок: iPhone через порт 443 (nginx), НЕ 18789 (только loopback).

## 12.08 — Секреты
- Ключи вынесены в `/etc/openclaw/secrets.json` (file-provider). DeepSeek отвечает 200.
- Поля protected (compaction, tools.agentToAgent, imageGenerationModel) — править напрямую в openclaw.json + restart, config.patch блокирует.

## 12.08–13.08 — Dайджест
- digest.py: TG-каналы (Медуза, Важные истории, The Bell, BAZA) + RSS (РБК `rssexport.rbc.ru/rbcnews/news/30/full.rss`, Коммерсантъ `kommersant.ru/rss/news.xml`) → саммари DeepSeek → курс ЦБ.
- Починен AI-саммари: скрипт не умел читать ключ из file-provider (ожидал строку) → научил читать secrets.json.
- Cron: daily-digest-morning, ежедневно 06:00 UTC (09:00 МСК), id e31154a5.

## 13.08 — Кросагентный доступ
- Включён tools.agentToAgent (enabled, allow [main, architect]) + tools.sessions.visibility=all для ручного запуска агента architect.
- Урок: allow-лист требует ВСЕХ участников пары (main и architect), иначе "denied by allow". Рестарт — полный (systemctl restart), SIGUSR1 не перечитывает reloadKind:none.

## 13.08 — MCP Context7
- Добавлен MCP-сервер context7 (`npx @upstash/context7-mcp`) — актуальная документация библиотек. Probe: 2 tools + resources + prompts.
- Vercel AI SDK НЕ ставим: OpenClaw не использует его внутри (замкнутый runtime); для мини-аппа не нужен (SSE уже умеет OpenClaw).

## 13.08 — Token-экономия (решение Дмитрия №2)
- Отменён кастомный семантический кэш ответов LLM и любые прокси/плагины перед DeepSeek (нет нативного семант. кэша в OpenClaw; SDK не имеет LLM-хука — опыт model-router).
- Включён штатный инструментальный кэш: tools.web.fetch.cacheTtlMinutes=60 и tools.web.search.cacheTtlMinutes=60 (результаты web-поиска/fetch кэшируются 1ч локально).
- Бытовые запросы (курс/дайджест/календарь) — напрямую через digest.py/gcal_reader.py, 0 токенов LLM. Глубокая аналитика — DeepSeek + штатная компакция.
- browser.headless=true (в конфиге `browser.headless`, НЕ plugins.entries.browser.config.headless — того не существует). Telegram остаётся на Long Polling (webhook НЕ включать).

## 13.08 — Tooling Stack (Blue Wave, решение Дмитрия)
- Принята архитектура субагентов (Router + Analyst/Coder/DevOps), ВАРИАНТ 1 (структура без роутинга): созданы `memory/agents/{analyst,coder,devops}.md` (роли, guardrails). Роутинг/параллельные LLM-вызовы НЕ включать (риск расхода токенов).
- Two-Tier Scraping зафиксирован в architecture.md: всегда HTTP Level 1 (curl) → browser Level 2 ТОЛЬКО при 403/429/JS.
- Capability Evolver = долговременная память (memory/ + MEMORY.md + agents/), отдельный плагин не нужен.
- GitHub: gh установлен (v2.97), роль coder через ветку+PR.
- ❌ Docker НЕ ставить (по решению Дмитрия). ❌ Tavily/Exa НЕ подключать (платно, дублирует web_search+Context7).
- Браузер (Puppeteer) уже встроен как Fallback Level 2, headless=true.
- GOG (Gmail/Docs/Sheets) отложен; Google Calendar работает.

## 13.08 — Аудит архитектора
- trustedProxies = [127.0.0.1] (nginx на loopback). WARN про proxy заголовки ушёл.
- browser.ssrfPolicy.dangerouslyAllowPrivateNetwork выключен (SSRF-риск); allowlist telegram оставлен.
- plugins.allow намеренно оставлен пустым (все грузятся; предложение архитектора ["codex","deepseek"] сломало бы остальные 7).
