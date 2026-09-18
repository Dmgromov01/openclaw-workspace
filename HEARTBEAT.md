<!-- project: github.com/Dmgromov01/openclaw-workspace -->
# Heartbeat checklist

- Если диск / > 80% — одно сообщение хозяину (не рестартить сервисы).
- Иначе — ничего не писать в Telegram (HEARTBEAT_OK).
- Без рассылок в группы. tg_send — только по прямой нужде из пункта выше.
- Gateway/хаб не рестартить из heartbeat: это дело cron-watchdog.
