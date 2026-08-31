# Run6 — gateway system-unit, watchdog, no approvals

Date: 2026-08-26/27. Deploy on the machine is done by agent main via `docs/PROMPT-run6.md`.
This repo is the agent workspace only. Do not touch hub code (`atlas-green-pearl-dawn`).

## Why

The bot "dies" when the **user** unit `openclaw-gateway` falls. Cannot revive from the phone without SSH.
Narrow allowlist + Telegram `/approve` on any binary outside the list → command hangs.

## Change

| Was | Becomes |
|---|---|
| gateway user-unit | system unit `/etc/systemd/system/openclaw-gateway.service` |
| linger unconfirmed | `loginctl enable-linger root` |
| watchdog hub only :8091 | plus :18789 and :8765, 3 fails, storm 60s |
| exec ask=on-miss + buttons | `tools.exec.mode=allowlist` (ask=off), telegram execApprovals=false |
| narrow allowlist | ls cat head tail df journalctl date uname free zramctl mkdir mv tar gpg git ss curl openclaw |
| photos sometimes Google | vision = DeepSeek flash-vision-exp |

Not in allowlist: rm reboot shutdown poweroff dd mkfs ufw iptables passwd chmod chown systemctl.

Not security=full.

## Files

- `services/openclaw-gateway.service` — system unit template (copy ExecStart from live user unit)
- `services/loop-watchdog.sh` — port checks
- `services/loop-watchdog-cron.sh` — reads hub `.env` (HubAlertsbot)
- `docs/PROMPT-run6.md` — prompt for the bot

## Cron

```
* * * * * /bin/sh /root/openclaw/services/loop-watchdog-cron.sh >/dev/null 2>&1
```

Do not replace or delete the hub watchdog.

## Revive after run6

```
systemctl restart openclaw-gateway
systemctl is-active openclaw-gateway
ss -lptn | grep 18789
```

No `--user`.
