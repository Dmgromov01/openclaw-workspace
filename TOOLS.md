# TOOLS.md — операционная шпаргалка

## Exec main
- tools.exec.mode=allowlist, ask=off; не security=full/ask=on-miss.
- Allowlist: ls cat head tail df journalctl date uname free zramctl mkdir mv tar gpg git ss curl openclaw.
- Не добавлять destructive/system команды.

## Модели
- Чат: DeepSeek v4 Flash; глубокие задачи: DeepSeek v4 Pro; фото: DeepSeek Flash Vision.
- Google Calendar — интеграция, не LLM.

## Сервисы
- Gateway: system unit openclaw-gateway, 127.0.0.1:18789.
- Hub: r2d2-hub, .output/server/index.mjs, 127.0.0.1:8091, https://hub.gbkz.uk, probes /healthz и /readyz.
- telegram-user-svc: 127.0.0.1:8765. Mini App и :8080 мертвы.

## Границы
- Hub agent: tools.allow=[].
- Оставить GitHub MCP, Context7, Parallel; Perplexity off.
- Конфиг OpenClaw — только openclaw config set + validate по прямому ТЗ.
