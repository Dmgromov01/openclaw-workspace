#!/bin/bash
# P1–P4: pull хаба, сборка Nitro, tick-cron, без рестарта шлюза.
# Только SSH. Не давать Telegram-агенту.
set -euo pipefail

HUB=/root/atlas-green-pearl-dawn
WS=/root/openclaw
ENVF="$HUB/.env"

echo "==== pull ===="
git -C "$HUB" pull --ff-only origin main
git -C "$WS" pull --ff-only origin main

echo "==== env (no secrets in git) ===="
touch "$ENVF"
chmod 600 "$ENVF"
grep -q '^HUB_ORIGIN=' "$ENVF" || echo 'HUB_ORIGIN=https://hub.gbkz.uk' >> "$ENVF"
if ! grep -q '^INTERNAL_CRON_SECRET=' "$ENVF"; then
  echo "INTERNAL_CRON_SECRET=$(openssl rand -hex 24)" >> "$ENVF"
  echo "wrote INTERNAL_CRON_SECRET"
fi
grep -q '^SESSION_TTL_SECONDS=' "$ENVF" || echo 'SESSION_TTL_SECONDS=43200' >> "$ENVF"

echo "==== build ===="
cd "$HUB"
export NODE_OPTIONS="${NODE_OPTIONS:---max-old-space-size=1536}"
npm run build
test -f "$HUB/.output/server/index.mjs"

echo "==== restart hub only ===="
systemctl restart r2d2-hub
for i in $(seq 1 40); do
  if curl -fsS --max-time 3 http://127.0.0.1:8091/ >/dev/null 2>&1; then
    echo "hub 200 after ${i}s"
    break
  fi
  sleep 1
done
curl -sI http://127.0.0.1:8091/ | head -8
systemctl is-active r2d2-hub

echo "==== tick cron every 5 min ===="
chmod +x "$HUB/scripts/hub-tick-cron.sh"
(crontab -l 2>/dev/null | grep -v hub-tick-cron; echo "*/5 * * * * /bin/sh $HUB/scripts/hub-tick-cron.sh >/dev/null 2>&1") | crontab -
crontab -l | grep hub-tick || true

echo "==== done (gateway not touched) ===="
echo "First visit to https://hub.gbkz.uk assigns the owner (name + PIN + Face ID)."
