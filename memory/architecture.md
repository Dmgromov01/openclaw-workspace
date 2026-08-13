# Architecture — пути, порты, guardrails

## Ключевые пути
- Конфиг OpenClaw: `~/.openclaw/openclaw.json` (protected — править только через config/CLI или напрямую для protected-полей + restart)
- Secrets: `/etc/openclaw/secrets.json` (file-provider; ключи deepseek_key, openrouter_key, google_key, proxyapi_key)
- Workspace агента: `/root/.openclaw/workspace` (AGENTS.md, SOUL.md, MEMORY.md, дневники `memory/YYYY-MM-DD.md`)
- Календарь: `/root/.openclaw/workspace/calendar/` (gcal_reader.py — read+add Google; digest.py — дайджест RSS+TG+курс)
- Личный TG: `/root/telegram-user-svc/server.py` (systemd `telegram-user-svc.service`, HTTP 127.0.0.1:8765)
- Плагины: `/root/.openclaw/plugins/` (menu-buttons, tg-user-tools, qwen-image-provider)
- Промпт архитектора: `/root/.openclaw/prompts/architect.md` = `/root/telegram-user-svc/AGENTS.md`

## Порты
- 18789: OpenClaw gateway (loopback only; наружу через nginx)
- 80/443: nginx (TLS Let's Encrypt, gbkz.uk → 127.0.0.1:18789)
- 7877: miniapp backend (через nginx /miniapp/)
- 8765: telegram-user-svc HTTP API
- 4001: Cloudflare WARP (обход блокировок, не помечается как дата-центр)

## Сеть/безопасность
- Tailscale: hiplet-109548 = 100.113.115.17 (tail6a4baa); vps-amnezia 100.79.152.33 — НЕ наш
- ufw: SSH 22, tailnet 100.64.0.0/10, 18789 только из tailnet. Default deny incoming
- Модель: deepseek/deepseek-chat (primary). DeepSeek НЕ принимает картинки

## Scraping Standard (Two-Tier, обязательный для кодинга/скрапинга)
- Level 1 (Fast): всегда сначала HTTP/cURL/urllib → вырезать чистый Markdown/текст. Быстро, экономно по RAM и токенам.
- Level 2 (Fallback): браузер (Puppeteer/plugin browser) ТОЛЬКО если HTTP дал 403/429 или требуется рендеринг JS.
- Основание: Web Scraping Standard, зафиксировано 13.08.

## Guardrails (жёсткие)
- В бот — ТОЛЬКО чистый результат (без логов/мыслей)
- Релиз в прод — только после явного «можно» (тест → отчёт → вопрос)
- protected-поля конфига (compaction, imageGenerationModel, tools.agentToAgent и др.) — править напрямую в openclaw.json + рестарт
- Не ставить зависимости в node_modules гейтвея OpenClaw (ломает runtime)
- WhatsApp закрыт, iCloud-календарь устарел (актуален Google)
