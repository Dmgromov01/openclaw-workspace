# AGENTS.md — Workspace

> Runtime-канон: `STATE.md`. Актуальный скилл хаба: `skills/r2d2-hub/SKILL.md`.

- Дневники: `memory/YYYY-MM-DD.md`; `MEMORY.md` только для главной сессии Дмитрия. Не коммитить runtime dreams/sessions/reports.
- Не править вручную `openclaw.json` и credentials; только `openclaw config set` + validate по прямому ТЗ.
- Не возвращать Google как LLM/vision/fallback.
- Не трогать ufw, zram, bind gateway, Parallel, Context7, GitHub MCP и tools агента hub без прямого ТЗ.
- Код хаба не трогать, кроме прямого ТЗ хозяина с явным списком файлов.
- Exec остаётся allowlist/ask=off; destructive/system команды не расширять.
- Перед systemd/cron/nginx: inspection, backup в `/root/_trash/ideal-YYYYMMDD/`, merge изменений.
- Gateway рестартовать только с SSH и явным разрешением; второй gateway не создавать.
- Mini App мёртв; семейный сайт — `https://hub.gbkz.uk`.
- Внешние действия требуют согласования; heartbeat не рестартует сервисы.
- Не кормить себя docs/archive/run6* и docs/archive/PROMPT-run6.md.
  Не запускать docs/archive/P0* / P1*.
