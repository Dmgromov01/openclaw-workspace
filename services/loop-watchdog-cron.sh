#!/bin/sh
# Cron-obertka: reads hub .env (HubAlertsbot), does not put token in crontab.
set -eu
set -a
if [ -f /root/atlas-green-pearl-dawn/.env ]; then
  . /root/atlas-green-pearl-dawn/.env
fi
set +a
WATCHDOG_STATE_DIR="${WATCHDOG_STATE_DIR:-/var/lib/r2d2/loop-watchdog}"
STORM_SEC="${STORM_SEC:-60}"
FAIL_THRESHOLD="${FAIL_THRESHOLD:-3}"
export TELEGRAM_BOT_TOKEN TELEGRAM_OWNER_ID WATCHDOG_STATE_DIR STORM_SEC FAIL_THRESHOLD
exec /bin/sh /root/openclaw/services/loop-watchdog.sh
