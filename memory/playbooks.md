# Playbooks — операционные руководства

## Стиль общения
- Кратко, структурированно, буллетами. Ноль маркетингового флаффа и воды.
- В Telegram — только чистый результат (без логов/мыслей/пояснений). Константа #1178.

## Стандарты кода
- Python/JS/редакции — строго по Two-Tier Scraping: HTTP Level 1 (curl/urllib) сначала; браузер Level 2 ТОЛЬКО при 403/429/JS.
- Все изменения кода — через git feature-ветку + PR. Без прямых правок на проде.
- Перед предложением кода: проверка синтаксиса (node --check / python3 -m py_compile / bash -n) + локальный прогон.

## Экстренный протокол (сбой сервиса)
1. Зафиксировать ошибку: `journalctl -u <unit> -n 30 --no-pager`.
2. Определить статус: `systemctl is-active openclaw-gateway r2d2-hub telegram-user-svc`.
3. Дать точные команды восстановления, НЕ «чинить вслепую».
4. Gateway — только system unit: `systemctl restart openclaw-gateway` с SSH и только по явному разрешению. User-unit не существует и не должен возвращаться.

## Частые операции
- Дайджест: `python3 /root/openclaw/calendar/digest.py` (--no-send для вывода без отправки).
- Календарь: `python3 /root/openclaw/calendar/gcal_reader.py today|week|list --days N`.
- Статус gateway: `systemctl status openclaw-gateway` / `openclaw status`.
- Секреты: `/etc/openclaw/secrets.json` (не логировать значения).
- Проверка диска: `df -h /`.
- Exec: без апрувов. allowlist в TOOLS.md. Вне списка — deny, не висеть.

## Guardrails (золотые правила)
- Не редактировать openclaw.json напрямую скриптами/агентами — только `openclaw config set` + проверка схемы ключа.
- Не возвращать Google в LLM/vision/fallback.
- Docker/Tavily/Exa — НЕ подключать (решение Дмитрия 13.08).
- Telegram — Long Polling, webhook НЕ включать.
- Код хаба не переписывать.
