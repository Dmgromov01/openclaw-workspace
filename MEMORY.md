# MEMORY.md — Долгосрочная память

## Кто мой человек
- Дмитрий; операторский бот `@Dmbotmy_bot` → main. Семейный сайт: `https://hub.gbkz.uk`.

## Неприкосновенное
- `openclaw.json`/credentials — только `openclaw config set` + validate по прямому ТЗ.
- Gateway — system unit и loopback; не создавать второй gateway.
- Hub agent `tools.allow=[]`; Google не возвращать в LLM/vision/fallback.

## Модели
- Обычный чат: DeepSeek v4 Flash; глубокие задачи: DeepSeek v4 Pro; фото: DeepSeek Flash Vision.

## Календарь
- Агент: Google user OAuth, `gcal_reader.py` today/week/list/add. Хаб: отдельный Google OAuth/PGLite flow. iCloud dormant.

## Урок 2026-08-31
- Старый skill хаба врал про Python Mini App; живой хаб — Node/Nitro `hub.gbkz.uk`.
- Дайджест и календарные уведомления не должны иметь параллельные cron-рассылки.
- Git без совпадающего `origin/main` не означает выполненную работу.
- Агент hub остаётся без tools; main остаётся операторским агентом.
- Runtime state, sessions и личные отчёты не коммитить.
