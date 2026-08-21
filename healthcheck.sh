#!/usr/bin/env bash
# healthcheck.sh — проверка всех рабочих инструментов OpenClaw-воркспейса.
# Запуск: bash /root/openclaw/healthcheck.sh  (exit 0 = всё ок, иначе проблемы)
# Cron: ежедневно (см. конец файла / crontab).
set -u
FAIL=0
log() { echo "[$(date +%H:%M:%S)] $*"; }
fail() { log "❌ $*"; FAIL=1; }
ok()   { log "✅ $*"; }

cd /root/openclaw

# 1. Компиляция КЛЮЧЕВЫХ скриптов (не всего дерева)
log "--- 1. Компиляция ключевых скриптов ---"
for f in \
  /root/openclaw/calendar/gcal_reader.py \
  /root/openclaw/calendar/digest.py \
  /root/openclaw/calendar/bot_sender.py \
  /root/openclaw/calendar/image_gen.py \
  /root/openclaw/miniapp/server.py \
  /root/openclaw/miniapp/auth.py \
  /root/openclaw/skills/excel_skills.py \
  /root/openclaw/update_bot_button.py; do
  [ -f "$f" ] && python3 -m py_compile "$f" 2>/dev/null && ok "py_compile: $(basename $f)" || fail "py_compile: $f"
done

# 2. Критичные файлы
log "--- 2. Критичные файлы ---"
for p in \
  /root/.openclaw/credentials/deepseek.key \
  /root/.openclaw/credentials/openrouter.key \
  /root/.openclaw/credentials/gcal/oauth-client.json \
  /root/.openclaw/credentials/gcal/tokens.json \
  /root/.openclaw/credentials/telegram-app.json \
  /root/.openclaw/.env \
  /root/openclaw/miniapp/auth.py \
  /root/openclaw/miniapp/server.py \
  /root/openclaw/calendar/gcal_reader.py \
  /root/openclaw/calendar/digest.py; do
  [ -f "$p" ] && ok "$p" || fail "нет файла: $p"
done

# 3. Сервисы
log "--- 3. Сервисы ---"
systemctl --user is-active miniapp.service >/dev/null 2>&1 && ok "miniapp.service" || fail "miniapp.service НЕ активен"
# telegram-user-svc: не systemd-юнит, а ручной процесс — проверяем порт 8765
(ss -tlnp 2>/dev/null | grep -q ":8765 ") && ok "telegram-user-svc (порт 8765)" || fail "telegram-user-svc НЕ слушает 8765"
systemctl --user is-active openclaw-gateway.service >/dev/null 2>&1 && ok "openclaw-gateway.service" || fail "openclaw-gateway.service НЕ активен"

# 4. Ключевые python-зависимости
log "--- 4. Зависимости (system python) ---"
python3 -c "import googleapiclient, google.oauth2" 2>/dev/null && ok "google-api (gcal)" || fail "google-api не установлен"
python3 -c "import openpyxl, pandas, duckdb, tabulate" 2>/dev/null && ok "excel (openpyxl/pandas/duckdb/tabulate)" || fail "excel-библиотеки не установлены"
python3 -c "import requests" 2>/dev/null && ok "requests" || fail "requests не установлен"

# 5. Smoke-тесты
log "--- 5. Smoke-тесты ---"
# gcal: сегодня
G=$(cd /root/openclaw/calendar && timeout 30 python3 gcal_reader.py today 2>&1)
if echo "$G" | grep -q "Сегодня"; then ok "gcal_reader today: $(echo "$G" | head -1)"; else fail "gcal_reader today: $G"; fi

# digest: сбор без отправки (первые строки)
D=$(cd /root/openclaw/calendar && timeout 60 python3 digest.py --no-send --hours 2 2>&1 | head -3)
if echo "$D" | grep -q "Дайджест"; then ok "digest.py собирается"; else fail "digest.py: $D"; fi

# miniapp: статика 200 + API защищён (401)
M=$(curl -s -o /dev/null -w "%{http_code}" -m 10 http://127.0.0.1:8080/)
[ "$M" = "200" ] && ok "miniapp статика 200" || fail "miniapp статика: $M"
M2=$(curl -s -o /dev/null -w "%{http_code}" -m 10 http://127.0.0.1:8080/api/calendar)
[ "$M2" = "401" ] && ok "miniapp API защищён (401)" || fail "miniapp API: $M2"

# telegram-user-svc: авторизован
T=$(curl -s -m 10 http://127.0.0.1:8765/auth/status 2>&1)
echo "$T" | grep -q '"authorized": true' && ok "telegram-user-svc авторизован" || fail "telegram-user-svc: $T"

log ""
if [ "$FAIL" = "0" ]; then
  log "🎉 ВСЕ ИНСТРУМЕНТЫ OK"
else
  log "⚠️ ЕСТЬ ПРОБЛЕМЫ (см. ❌ выше)"
fi
exit $FAIL
