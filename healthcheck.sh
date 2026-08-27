#!/usr/bin/env bash
# healthcheck.sh — проверка рабочих инструментов OpenClaw-воркспейса.
set -u
FAIL=0
log() { echo "[$(date +%H:%M:%S)] $*"; }
fail() { log "FAIL $*"; FAIL=1; }
ok()   { log "OK $*"; }

cd /root/openclaw

log "--- services ---"
if systemctl --user is-enabled miniapp.service >/dev/null 2>&1; then
  systemctl --user is-active miniapp.service >/dev/null 2>&1 && ok "miniapp.service" || fail "miniapp.service not active"
else
  ok "miniapp.service disabled (planned)"
fi
systemctl is-active telegram-user-svc.service >/dev/null 2>&1 && ok "telegram-user-svc.service" || fail "telegram-user-svc.service not active"
(ss -tlnp 2>/dev/null | grep -q ":8765 ") && ok "telegram-user-svc :8765" || fail "telegram-user-svc not on 8765"
if systemctl is-active openclaw-gateway.service >/dev/null 2>&1; then
  ok "openclaw-gateway.service (system)"
elif systemctl --user is-active openclaw-gateway.service >/dev/null 2>&1; then
  ok "openclaw-gateway.service (user — run6 not done yet)"
else
  fail "openclaw-gateway.service not active"
fi
(ss -tlnp 2>/dev/null | grep -q ":18789 ") && ok "gateway :18789" || fail "gateway not on 18789"
systemctl is-active r2d2-hub.service >/dev/null 2>&1 && ok "r2d2-hub.service" || fail "r2d2-hub.service not active"

/usr/sbin/ufw status 2>/dev/null | grep -q "Status: active" && ok "ufw active" || fail "ufw not active"
if ss -tlnp 2>/dev/null | grep -q ":8080 "; then
  ss -tlnp 2>/dev/null | grep ":8080 " | grep -q "127.0.0.1" && ok "miniapp loopback" || fail "miniapp not loopback"
else
  ok "port 8080 closed (miniapp off)"
fi

T=$(curl -s -m 10 http://127.0.0.1:8765/auth/status 2>&1)
echo "$T" | grep -q '"authorized": true' && ok "telegram-user-svc authorized" || fail "telegram-user-svc: $T"

if [ "$FAIL" = "0" ]; then
  log "ALL OK"
else
  log "PROBLEMS above"
fi
exit $FAIL
