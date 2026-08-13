# Playbooks — операционные руководства

## Стиль общения
- Кратко, структурированно, буллетами. Ноль маркетингового флаффа и воды.
- В Telegram — только чистый результат (без логов/мыслей/пояснений). Константа #1178.

## Стандарты кода
- Python/JS/редакции — строго по Two-Tier Scraping: HTTP Level 1 (curl/urllib) сначала; браузер Level 2 ТОЛЬКО при 403/429/JS.
- Все изменения кода — через git feature-ветку + PR. Без прямых правок на проде.
- Перед предложением кода: проверка синтаксиса (node --check / python3 -m py_compile / bash -n) + локальный прогон.

## Экстренный протокол (сбой сервиса)
1. Зафиксировать ошибку: `journalctl -u <unit> -n 30 --no-pager` или `tail -n 30 /tmp/openclaw/openclaw-*.log` / нужного лога.
2. Определить статус: `systemctl --user is-active <unit>`.
3. Дать точные команды восстановления (с указанием unit и командой), НЕ «починить вслепую».
4. Рестарт прод-гейтвея — только с явного «можно» (правило релиза). `systemctl --user restart openclaw-gateway.service`, НЕ SIGUSR1 для reloadKind:none.

## Частые операции
- Дайджест: `python3 /root/.openclaw/workspace/calendar/digest.py` (--no-send для вывода без отправки).
- Календарь: `python3 /root/.openclaw/workspace/calendar/gcal_reader.py today|week|list --days N`; add для событий.
- Статус gateway: `systemctl --user status openclaw-gateway.service` / `openclaw status`.
- Секреты: `/etc/openclaw/secrets.json` (не логировать значения).
- Проверка диска: `df -h /`; очистка старых логов: `find /tmp/openclaw/ -type f -mtime +2 -delete`.

## Guardrails (золотые правила)
- Не редактировать openclaw.json напрямую скриптами/агентами — только `openclaw config set` + проверка схемы ключа.
- protected-поля (compaction, tools.agentToAgent и др.) — прямое редактирование + рестарт, после «можно».
- Docker/Tavily/Exa — НЕ подключать (решение Дмитрия 13.08).
- Telegram — Long Polling, webhook НЕ включать.
