# P2 — секреты и exec (решение)

Снимок: 28.08.2026. Не кормить этот файл Telegram-агенту.

## SecretRefs

Ключи OpenClaw живут в `/root/.openclaw/openclaw.json`. Их **не коммитить**.

Предпочтение: `SecretRef` (file/env) для:

- `gateway.auth.token`
- токен `@Dmbotmy_bot`
- токен `@HubAlertsbot`
- любые API-ключи провайдеров

Файлы секретов: `/root/.openclaw/secrets/` chmod 600, не в git.

Перенос делать **только с SSH**, не через агента `main`. После смены токена шлюза — `systemctl restart openclaw-gateway` с SSH.

Хаб: `INTERNAL_CRON_SECRET` и `HUB_ORIGIN=https://hub.gbkz.uk` в `/root/atlas-green-pearl-dawn/.env` (EnvironmentFile юнита). Не в репозитории.

## exec.ask

Оставляем **ask=off**, security=allowlist.

В allowlist уже есть рабочие бинари, включая `curl git tar gpg mv`. Их не спрашиваем.

По-прежнему **нельзя** (не добавлять): `rm reboot shutdown poweroff dd mkfs ufw iptables passwd chmod chown systemctl loginctl systemd-run`.

Не `security=full`. Не `ask=on-miss` — висящие апрувы выглядят как «бот умер».

## Агент hub

`tools.allow=[]` — не трогать. Семейный чат сайта без exec/files.

## Порты

`:18789` и `:8091` только loopback. WAN — nginx TLS. ufw/zram/nginx bind не менять этим коммитом.
