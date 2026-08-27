# STOP — не кормить это @Dmbotmy_bot

Run6-промпт убил шлюз: агент изнутри gateway делал `openclaw config set` + `systemctl --user stop openclaw-gateway`.

Живые правки шлюза / systemd / watchdog — **только root в SSH**.

Скрипт: [`docs/run6-root.sh`](run6-root.sh)
