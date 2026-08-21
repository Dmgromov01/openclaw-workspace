#!/usr/bin/env bash
# Еженедельный clawpatch review воркспейса (пн 05:00 UTC, cron)
set -uo pipefail
export DEEPSEEK_API_KEY="$(cat /root/.openclaw/credentials/deepseek.key)"
cd /root/openclaw
RUN_LOG="/root/openclaw/.clawpatch/weekly.log"
echo "=== $(date -u +%F\ %T) review ===" >> "$RUN_LOG"
clawpatch review --limit 20 >> "$RUN_LOG" 2>&1
clawpatch report --json >> "$RUN_LOG" 2>&1
echo "done rc=$?" >> "$RUN_LOG"
