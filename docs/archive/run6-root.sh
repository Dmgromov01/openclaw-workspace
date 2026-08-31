#!/bin/bash
# Run ONLY as root on hiplet via SSH. Never via Telegram / OpenClaw exec.
# Migrates openclaw-gateway user-unit -> system-unit and installs :18789/:8765 watchdog.
set -u
export XDG_RUNTIME_DIR="${XDG_RUNTIME_DIR:-/run/user/0}"

wait_port() {
  local n="${1:-30}"
  local i
  for i in $(seq 1 "$n"); do
    if ss -lptn | grep -q ':18789'; then
      echo "port 18789 bound after ${i}s"
      return 0
    fi
    sleep 1
  done
  return 1
}

rollback_user() {
  echo "ROLLBACK: stopping system unit, starting user unit"
  systemctl stop openclaw-gateway.service 2>/dev/null || true
  sleep 2
  systemctl --user unmask openclaw-gateway.service 2>/dev/null || true
  systemctl --user start openclaw-gateway.service || true
  wait_port 30 || true
  systemctl --user is-active openclaw-gateway.service || true
  ss -lptn | grep 18789 || true
}

mkdir -p /var/tmp/openclaw-compile-cache /var/lib/r2d2/loop-watchdog

install -m 644 /root/openclaw/services/openclaw-gateway.service /etc/systemd/system/openclaw-gateway.service
systemctl daemon-reload

echo "-- stop user unit --"
systemctl --user stop openclaw-gateway.service || true
wait_port 5 && {
  echo "port 18789 still busy after user stop; abort"
  ss -lptn | grep 18789 || true
  rollback_user
  exit 1
}
# wait_port returns 0 if bound — here we want it GONE
if ss -lptn | grep -q ':18789'; then
  echo "port 18789 still busy after user stop; abort"
  ss -lptn | grep 18789 || true
  rollback_user
  exit 1
fi

echo "-- start system unit --"
systemctl enable --now openclaw-gateway.service
if ! wait_port 30; then
  echo "system unit did not bind :18789"
  systemctl --no-pager --full status openclaw-gateway.service || true
  journalctl -u openclaw-gateway -n 40 --no-pager || true
  rollback_user
  exit 1
fi
if ! systemctl is-active --quiet openclaw-gateway.service; then
  echo "system unit not active"
  rollback_user
  exit 1
fi

echo "-- disable user unit --"
systemctl --user disable openclaw-gateway.service || true
systemctl --user mask openclaw-gateway.service || true

chmod +x /root/openclaw/services/loop-watchdog.sh /root/openclaw/services/loop-watchdog-cron.sh
(crontab -l 2>/dev/null | grep -v 'loop-watchdog-cron.sh'; echo '* * * * * /bin/sh /root/openclaw/services/loop-watchdog-cron.sh >/dev/null 2>&1') | crontab -

openclaw approvals allowlist remove --agent main --gateway /usr/bin/systemctl 2>/dev/null || true
openclaw approvals allowlist remove --agent main --gateway /usr/bin/loginctl 2>/dev/null || true
openclaw approvals allowlist remove --agent main --gateway /usr/bin/systemd-run 2>/dev/null || true

echo "==== verify ===="
echo -n "system: "; systemctl is-active openclaw-gateway
echo -n "system enabled: "; systemctl is-enabled openclaw-gateway
echo -n "user: "; systemctl --user is-active openclaw-gateway || true
ss -lptn | grep -E '18789|8765' || true
crontab -l | grep loop-watchdog || true
openclaw channels status --probe || true
