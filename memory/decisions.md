# Decisions — журнал ключевых архитектурных решений

## 12.08 — Домен и вход
- gbkz.uk (Cloudflare → nginx → OpenClaw 18789) — основной домен.
- auth.mode = token; iPhone через wss://gbkz.uk:443, НЕ 18789.

## 12.08 — Секреты
- Ключи в `/etc/openclaw/secrets.json` (file-provider).
- protected-поля — прямое редактирование + restart, config.patch блокирует.

## 13.08 — MCP / инструменты
- Context7 MCP оставлять. Docker/Tavily/Exa НЕ ставить.
- Telegram — Long Polling, webhook НЕ включать.
- Google Calendar работает как календарь хаба, не как LLM.

## 27.08 вечер — run6 (апрувы off, gateway system)
- Хозяин: убрать апрувы exec. Канон OpenClaw 2026.7: `tools.exec.mode=allowlist` (= security=allowlist + ask=off). Не full.
- Telegram execApprovals.enabled=false, чтобы не висеть на /approve.
- Gateway с user-юнита на system (как r2d2-hub). linger root. Watchdog :18789+:8765, 3 провала, антишторм 60с.
- Vision = DeepSeek, не Google. Генерация картинок = OpenRouter Gemini Flash. gcal хаба не трогать.
- Код хаба / ufw / zram / Parallel / Context7 / GitHub MCP / агент hub без tools — не трогать.
