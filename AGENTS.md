<!-- project: github.com/Dmgromov01/openclaw-workspace -->
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

## Composio
- Для работы с внешними приложениями использовать установленный Composio plugin и локальный CLI, даже если пользователь не называет Composio.
- Перед первой операцией в новом execution environment проверить `composio --version` (требуется >= 0.4.0) и `composio whoami`; использовать полный путь `/root/.composio/cli/composio`, если bare `composio` блокируется allowlist.
- Выбирать узкий workflow: известный slug → `execute`; неизвестный инструмент → `search`, затем схема и только потом выполнение.
- OAuth/link, установка и обновление CLI — только по прямой команде владельца; authorization URL показывать только владельцу в личном чате.
- Не повторять неопределённую запись через другой интерфейс; перед внешними изменениями явно подтверждать действие, если оно не было прямо запрошено.
- Composio использовать для внешних приложений, не для локальных файлов, shell-команд или публичного web-поиска. Наличие Composio не означает автоматическую изоляцию произвольного bash: sandboxing считать гарантированным только при отдельной подтверждённой настройке.
- Не менять существующие модели, agents, skills и secrets при настройке Composio без отдельного прямого запроса.

## Tools

### Local notes (migrated from TOOLS.md)

# TOOLS.md — операционная шпаргалка

## Exec main
- tools.exec.mode=allowlist, ask=off; не security=full/ask=on-miss.
- Allowlist: ls cat head tail df journalctl date uname free zramctl mkdir mv tar gpg git ss curl openclaw.
- Не добавлять destructive/system команды.

## Модели
- Чат и vision: DeepSeek V4.1 Flash (`deepseek/deepseek-flash`). V4 Pro выведен: с 14.09.2026 `deepseek-v4-pro` идёт на V4.1 Flash.
- Google Calendar — интеграция, не LLM.

## Сервисы
- Gateway: system unit openclaw-gateway, 127.0.0.1:18789.
- Hub: r2d2-hub, .output/server/index.mjs, 127.0.0.1:8091, https://hub.gbkz.uk, probes /healthz и /readyz.
- telegram-user-svc: 127.0.0.1:8765. Mini App и :8080 мертвы.

## Границы
- Hub agent: tools.allow=[].
- Оставить GitHub MCP, Context7, Parallel; Perplexity off.
- Конфиг OpenClaw — только openclaw config set + validate по прямому ТЗ.

## Current state vs memory (правило 2026-09-16)

- `workspace/CURRENT_SYSTEM_STATE.md` и текущая runtime-конфигурация авторитетны для ТЕКУЩЕГО состояния OpenClaw.
- MEMORY (`MEMORY.md`, `memory/*.md`) авторитетна для исторического, пользовательского, проектного и ранее подтверждённого контекста.
- Никогда не выводить текущее состояние плагина/инструмента/модели/агента/прав из исторической памяти.
- Конфликт: историческая память = историческая информация; CURRENT_SYSTEM_STATE = текущее состояние.
- Текущее состояние не проверено — сказать «неизвестно», не выдумывать.
- `CURRENT_SYSTEM_STATE.md` только генерируется через `workspace/system_state.py`; вручную не править.
- MEMORY.md — durable-факты/предпочтения/решения; `memory/YYYY-MM-DD.md` — рабочие заметки дня. MEMORY.md не превращать в транскрипт.

