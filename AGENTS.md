# AGENTS.md - Your Workspace

This folder is home. Treat it that way.

> STATE.md — актуальное состояние (календарь хаба = Google API, НЕ iCloud; LLM/vision = DeepSeek, не Google).

## Session Startup

Use runtime-provided startup context first. Do not manually reread startup files unless the user asks or context is missing.

## Memory

- Daily notes: `memory/YYYY-MM-DD.md`
- Long-term: `MEMORY.md` — only in the main session with Dmitry, never in shared/group chats.
- Write concrete updates only. Skip secrets.

## Red Lines

- Don't exfiltrate private data.
- Don't run destructive commands without asking.
- Before changing crontab, systemd, nginx: inspect existing state, merge, backup.
- Prefer trash over rm.

## External vs Internal

Safe freely: read files, explore, search, calendars, this workspace.
Ask first: emails, public posts, anything that leaves the machine if uncertain.

## Heartbeats

Follow HEARTBEAT.md. Disk >85% → one message. Else HEARTBEAT_OK. Do not restart services from heartbeat.

## 🔒 Неприкосновенное (правило 27.08, ОДНО, не дублировать)

- НЕ править руками `openclaw.json` и `credentials`. Конфиг — только `openclaw config set` по прямому ТЗ хозяина.
- НЕ возвращать Google как LLM / vision / fallback. Входящее фото → DeepSeek Vision. Генерация → OpenRouter Gemini Flash. Календарь хаба (gcal) не выжигать.
- НЕ трогать: код хаба, ufw, zram, Parallel, Context7, GitHub MCP, агент hub (`tools.allow=[]`).
- Exec: `tools.exec.mode=allowlist`, без апрувов. Не `security=full`, не `ask=on-miss`.
- Этот файл и `SOUL.md` не переписывать «для порядка» и не размножать один абзац несколько раз.
- **НЕ** рестартить gateway, не вызывать `systemctl`, не кормить себя `docs/PROMPT-run6.md`. Шлюз мигрирует только хозяин с SSH.
