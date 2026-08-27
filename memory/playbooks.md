# Playbooks — операционные руководства

## Стиль общения
- Кратко, структурированно, буллетами. Ноль маркетингового флаффа и воды.
- В Telegram — только чистый результат (без логов/мыслей/пояснений). Константа #1178.

## Стандарты кода
- Python/JS/редакции — строго по Two-Tier Scraping: HTTP Level 1 (curl/urllib) сначала; браузер Level 2 ТОЛЬКО при 403/429/JS.
- Все изменения кода — через git feature-ветку + PR. Без прямых правок на проде.
- Перед предложением кода: проверка синтаксиса (node --check / python3 -m py_compile / bash -n) + локальный прогон.

## Экстренный протокол (сбой сервиса)
1. Зафиксировать ошибку: `journalctl -u <unit> -n 30 --no-pager` (после run6 gateway без --user).
2. Определить статус: `systemctl is-active openclaw-gateway r2d2-hub telegram-user-svc`.
3. Дать точные команды восстановления, НЕ «починить вслепую».
4. Рестарт шлюза: `systemctl restart openclaw-gateway` (без --user, без SIGUSR1).
5. Если system-юнит ещё не переведён: `export XDG_RUNTIME_DIR=/run/user/0; systemctl --user restart openclaw-gateway`.

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
