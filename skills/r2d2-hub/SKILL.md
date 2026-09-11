---
name: r2d2-hub
description: Семейный хаб hub.gbkz.uk — контракт развёртывания, auth (Face ID/PIN/инвайт), чат через gateway, запреты и probes.
---

# R2D2 Hub

Семейный хаб — сайт `https://hub.gbkz.uk`, не Telegram Mini App.

## Живой контракт

- Репозиторий: `Dmgromov01/atlas-green-pearl-dawn`; production: `/root/atlas-green-pearl-dawn`.
- Runtime: systemd `r2d2-hub`, Node/TanStack Start Nitro `.output/server/index.mjs`, `127.0.0.1:8091`, nginx TLS.
- Auth: Face ID + PIN + одноразовый инвайт через hub-auth. Не Telegram initData и не HMAC WebAppData.
- Чат: gateway `127.0.0.1:18789`, session `hub:<userId>`, `tool_choice: none`.
- Агент `hub`: `tools.allow=[]`. Оператор: `@Dmbotmy_bot` → `main`; пейджер: `@HubAlertsbot`.
- Календарь UI: отдельный Google OAuth/PGLite flow хаба. iCloud dormant; `hub_icloud` не drop.
- Probes: `/healthz`, `/readyz`; backup: `/var/backups/r2d2`.

## Запреты

- Mini App, `miniapp.service`, `:8080`, Python `miniapp/server.py`, `/miniapp/`, HMAC WebAppData как вход — мертвы; не ставить и не чинить.
- Не открывать `8091`/`18789` наружу, не менять Nitro preset/bind, не создавать второй gateway.
- Не включать tools агенту hub.
