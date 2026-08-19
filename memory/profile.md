# Profile — система и окружение

## Сервер
- VPS vps-7182, IP 138.124.180.178 (Франкфурт DE), Ubuntu 24.04, 2 vCPU / 2 GB RAM / 20 GB SSD (старый IP 45.95.2.246 — устарел, не использовать)
- Host Tailscale: hiplet-109548 = 100.113.115.17 (таилнет tail6a4baa)
- Swap 2GB создан

## Стек
- Node.js v24.19.0, npm/npx 11.17.0, Python3
- OpenClaw gateway: user-systemd юнит `openclaw-gateway.service`, порт 18789 (loopback)
- Модель: deepseek/deepseek-chat (прямой API, 1M ctx). Провайдеры: deepseek · openrouter · google
- DeepSeek не принимает картинки — для image использовать GPT-4o/Gemini

## Домен/вход
- gbkz.uk (Cloudflare DNS+прокси) → nginx (TLS Let's Encrypt) → 127.0.0.1:18789
- gateway.remote.url = wss://gbkz.uk; auth mode = token

## Интеграции
- Календарь: Google Calendar (dmgromov03@gmail.com), `gcal_reader.py` — читает + add
- Telegram-бот: владелец id 1916536646, bot @Dmbotmy_bot
- Личный TG (MTProto): telegram-user-svc, HTTP 127.0.0.1:8765, systemd
- MCP: context7 (док-сервер, npx @upstash/context7-mcp)

## Пользователь
- Дмитрий (@Dm_GRM), русскоязычный, Europe/Moscow
