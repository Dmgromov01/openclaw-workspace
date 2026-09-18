#!/bin/sh
# Проверка диска: если df / > 85% — алерт в @HubAlertsbot (владельцу).
# Сервисы НЕ рестартит. Токен берётся из .env хаба (не светится в crontab).
set -eu
THRESHOLD="${DISK_THRESHOLD_PCT:-85}"
ENV_FILE=/root/atlas-green-pearl-dawn/.env
if [ -f "$ENV_FILE" ]; then
  set -a
  # shellcheck disable=SC1091
  . "$ENV_FILE"
  set +a
fi
PCT=$(df / | awk 'NR==2 {gsub("%","",$5); print $5}')
PCT=${PCT:-0}
if [ "$PCT" -gt "$THRESHOLD" ]; then
  token="${TELEGRAM_BOT_TOKEN:-}"
  chat="${TELEGRAM_OWNER_ID:-}"
  if [ -n "$token" ] && [ -n "$chat" ]; then
    curl -sS -o /dev/null --max-time 8 -X POST \
      "https://api.telegram.org/bot${token}/sendMessage" \
      -H 'content-type: application/json' \
      -d "{\"chat_id\":${chat},\"text\":$(printf '%s' "⚠️ Диск на мини-ПК: / заполнен на ${PCT}% (порог ${THRESHOLD}%)" | python3 -c 'import json,sys; print(json.dumps(sys.stdin.read()))'),\"disable_web_page_preview\":true}" || true
  fi
fi
