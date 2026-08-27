# Profile — система и окружение

## Сервер
- VPS, IP 138.124.180.178 (Франкфурт DE), Ubuntu 24.04
- Tailscale: tail6a4baa.ts.net (хост в git-коммитах hiplet-109548; в handoff фигурировал hiplet-112102)
- RAM ~3.8G, zram0 ~2G priority 100. Swapfile не ставить.
- Ядро после ребута 27.08: 6.8.0-138-generic

## Стек
- OpenClaw 2026.7.1-2, workspace `/root/openclaw`, конфиг `/root/.openclaw/openclaw.json`
- Gateway: цель = system-юнит `openclaw-gateway` :18789 loopback, auth=token, chatCompletions вкл
- Хаб: system-юнит `r2d2-hub` :8091 → https://hub.gbkz.uk
- telegram-user-svc: 127.0.0.1:8765
- miniapp: disabled

## Модели (хозяин 27.08)
- чат/heartbeat: deepseek/deepseek-v4-flash
- глубоко: deepseek/deepseek-v4-pro
- входящее фото: deepseek/deepseek-v4-flash-vision-exp
- генерация картинок: OpenRouter → Gemini Flash image
- Google как LLM/vision — не нужен. Календарь хаба = gcal отдельно.

## Домен/вход
- gbkz.uk (Cloudflare DNS+прокси) → nginx (TLS) → 127.0.0.1:18789
- хаб: https://hub.gbkz.uk (сайт, не Mini App)
- iPhone сопряжён как node+operator

## Интеграции
- Календарь хаба: Google Calendar
- Telegram: хозяин 1916536646, оператор @Dmbotmy_bot, пейджер @HubAlertsbot
- MCP: Context7 + GitHub. Parallel on. Perplexity off
- Ключи вне git: `/root/.openclaw/credentials/`, `/etc/openclaw/secrets.json`

## Пользователь
- Дмитрий (@Dm_GRM), русскоязычный, Europe/Moscow
