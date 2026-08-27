#!/bin/sh
# Watchdog OpenClaw gateway (:18789) and telegram-user-svc (:8765).
# Does not touch r2d2-hub. Does not print secrets.
# 3 consecutive fails -> restart that unit.
# Alert storm window: 60s (not 10 min).
# Env: TELEGRAM_BOT_TOKEN + TELEGRAM_OWNER_ID (HubAlertsbot),
#      WATCHDOG_STATE_DIR (default /var/lib/r2d2/loop-watchdog),
#      STORM_SEC (default 60), FAIL_THRESHOLD (default 3).

set -eu

STATE_DIR="${WATCHDOG_STATE_DIR:-/var/lib/r2d2/loop-watchdog}"
STORM_SEC="${STORM_SEC:-60}"
FAIL_THRESHOLD="${FAIL_THRESHOLD:-3}"
mkdir -p "$STATE_DIR"

alert() {
  msg="$1"
  last="$STATE_DIR/last-alert"
  now=$(date +%s)
  if [ -f "$last" ]; then
    prev=$(cat "$last" 2>/dev/null || echo 0)
    if [ $((now - prev)) -lt "$STORM_SEC" ]; then
      echo "$msg (suppressed storm)"
      return 0
    fi
  fi
  echo "$now" > "$last"
  token="${TELEGRAM_BOT_TOKEN:-}"
  chat="${TELEGRAM_OWNER_ID:-}"
  if [ -n "$token" ] && [ -n "$chat" ]; then
    curl -sS -o /dev/null --max-time 8 -X POST \
      "https://api.telegram.org/bot${token}/sendMessage" \
      -H 'content-type: application/json' \
      -d "{\"chat_id\":${chat},\"text\":$(printf '%s' "$msg" | python3 -c 'import json,sys; print(json.dumps(sys.stdin.read()))'),\"disable_web_page_preview\":true}" \
      || true
  fi
  echo "$msg"
}

port_up() {
  port="$1"
  ss -lptn 2>/dev/null | grep -q ":${port} " && return 0
  ss -lptn 2>/dev/null | grep -q ":${port}$" && return 0
  return 1
}

restart_gateway() {
  if systemctl list-unit-files --type=service 2>/dev/null | grep -q '^openclaw-gateway.service'; then
    if systemctl is-enabled openclaw-gateway.service >/dev/null 2>&1 \
       || systemctl is-active openclaw-gateway.service >/dev/null 2>&1; then
      systemctl restart openclaw-gateway.service || true
      return 0
    fi
  fi
  export XDG_RUNTIME_DIR="${XDG_RUNTIME_DIR:-/run/user/0}"
  systemctl --user restart openclaw-gateway.service || true
}

check_one() {
  name="$1"
  port="$2"
  failf="$STATE_DIR/fail-$name"
  if port_up "$port"; then
    echo 0 > "$failf"
    echo "ok $name :$port"
    return 0
  fi
  n=$(cat "$failf" 2>/dev/null || echo 0)
  n=$((n + 1))
  echo "$n" > "$failf"
  echo "fail $name :$port ($n/$FAIL_THRESHOLD)"
  if [ "$n" -lt "$FAIL_THRESHOLD" ]; then
    return 0
  fi
  echo 0 > "$failf"
  case "$name" in
    gateway)
      alert "OpenClaw gateway :${port} down ($FAIL_THRESHOLD fails). Restarting openclaw-gateway."
      restart_gateway
      sleep 5
      if port_up "$port"; then
        alert "Gateway :${port} listening again."
      else
        alert "Gateway :${port} did not come back. Need SSH."
      fi
      ;;
    tgsvc)
      alert "telegram-user-svc :${port} down ($FAIL_THRESHOLD fails). Restarting telegram-user-svc."
      systemctl restart telegram-user-svc.service || true
      sleep 5
      if port_up "$port"; then
        alert "telegram-user-svc :${port} listening again."
      else
        alert "telegram-user-svc :${port} did not come back. Need SSH."
      fi
      ;;
  esac
}

check_one gateway 18789
check_one tgsvc 8765
