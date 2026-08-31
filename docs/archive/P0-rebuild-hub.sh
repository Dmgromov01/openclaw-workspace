#!/bin/bash
# P0: rebuild hub off vercel-preview onto Nitro node-server.
# Run as root on hiplet. Do NOT feed this to the Telegram bot.
set -euo pipefail

HUB=/root/atlas-green-pearl-dawn
WS=/root/openclaw
UNIT=/etc/systemd/system/r2d2-hub.service

echo "==== pull ===="
git -C "$HUB" pull --ff-only origin main
git -C "$WS" pull --ff-only origin main

echo "==== backup pglite (once) ===="
mkdir -p /var/backups/r2d2
if [ -d /var/lib/r2d2/pglite ]; then
  tar -C /var/lib/r2d2 -czf "/var/backups/r2d2/pglite-pre-node-$(date +%Y%m%d-%H%M).tar.gz" pglite || true
fi
ls -lh /var/backups/r2d2 | tail -n 8 || true

echo "==== build (old hub stays up) ===="
cd "$HUB"
export NODE_OPTIONS="${NODE_OPTIONS:---max-old-space-size=1536}"
npm run build
test -f "$HUB/.output/server/index.mjs"

echo "==== install unit ===="
cp "$WS/services/r2d2-hub.service" "$UNIT"
systemctl daemon-reload

echo "==== switch ===="
systemctl restart r2d2-hub
for i in $(seq 1 40); do
  if curl -fsS --max-time 3 http://127.0.0.1:8091/ >/dev/null 2>&1; then
    echo "hub 200 after ${i}s"
    break
  fi
  sleep 1
done
curl -sI http://127.0.0.1:8091/ | head -8
ss -lptn | grep 8091 || true
systemctl is-active r2d2-hub

echo "==== cron watchdog + nightly backup ===="
chmod +x "$HUB/scripts/hub-watchdog.sh" "$HUB/scripts/hub-watchdog-cron.sh" "$HUB/scripts/hub-backup.sh"
(crontab -l 2>/dev/null | grep -v hub-watchdog; echo "* * * * * /bin/sh $HUB/scripts/hub-watchdog-cron.sh >/dev/null 2>&1") | crontab -
(crontab -l 2>/dev/null | grep -v hub-backup; echo "15 2 * * * /bin/sh $HUB/scripts/hub-backup.sh >/var/log/hub-backup.log 2>&1") | crontab -
crontab -l | grep -E 'hub-watchdog|hub-backup'

echo "==== drop vercel leftover only if new server is healthy ===="
if curl -fsS --max-time 5 http://127.0.0.1:8091/ >/dev/null; then
  if ss -lptn | grep -q '127.0.0.1:8091'; then
    rm -rf "$HUB/.vercel/output"
    echo "removed .vercel/output"
  else
    echo "KEEP .vercel/output: hub is not on 127.0.0.1:8091"
  fi
else
  echo "KEEP .vercel/output: health check failed"
  exit 1
fi

echo "==== done ===="
systemctl status r2d2-hub --no-pager | head -18
