# TOOLS.md — локальная шпаргалка

## Exec (агент main, run6)

- `tools.exec.mode=allowlist` → security=allowlist, ask=off. Апрувов нет.
- telegram `execApprovals.enabled=false`
- allowlist: ls cat head tail df journalctl date uname free zramctl mkdir mv tar gpg git ss curl openclaw
- запрещено даже спрашивать: rm reboot shutdown poweroff dd mkfs ufw iptables passwd chmod chown systemctl
- не security=full, не ask=on-miss
- вне списка → сразу deny, без зависания и без кнопки /approve

## Модели (не Google как LLM/vision)

- чат/heartbeat: deepseek/deepseek-v4-flash
- глубоко: deepseek/deepseek-v4-pro
- входящее фото: deepseek/deepseek-v4-flash-vision-exp (не CLI media, не google vision)
- генерация картинок: OpenRouter → Gemini Flash image
- Google Calendar хаба = gcal, это не LLM

## Сервисы

- gateway: system-юнит `openclaw-gateway` :18789 loopback. Рестарт: `systemctl restart openclaw-gateway` (без --user)
- хаб: system-юнит `r2d2-hub` :8091 → https://hub.gbkz.uk
- telegram-user-svc: 127.0.0.1:8765
- miniapp: disabled, :8080 не слушает
- watchdog хаба: cron каждую минуту, 3 провала → restart r2d2-hub
- watchdog шлюза: `services/loop-watchdog-cron.sh` :18789 и :8765, антишторм 60с, алерты @HubAlertsbot

## MCP / поиск

- оставить: GitHub MCP, Context7, Parallel
- Perplexity off
- агент hub: tools.allow=[] — не включать

## Node (iPhone)

- camera.snap разрешён
- sms / contacts / callLog — deny
