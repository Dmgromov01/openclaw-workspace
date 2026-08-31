# STATE.md — актуальное runtime-состояние

> Это единственный канон для живой инфраструктуры.

## Календарь
- Агент: Google Calendar user OAuth (`oauth-client.json` + `tokens.json`), Europe/Moscow; CLI `gcal_reader.py` поддерживает today/week/list/add.
- Hub: отдельный Google OAuth/PGLite flow. iCloud UI/автосинк dormant; `hub_icloud` не drop.

## Модели и память
- Чат: DeepSeek v4 Flash; глубокие задачи: DeepSeek v4 Pro; vision: DeepSeek Flash Vision.
- Builtin memory search: Jina `jina-embeddings-v3`, only `memory`, `sessionMemory=false`, `keepRecentTokens=80000`.
- Google не использовать как LLM/vision/fallback.

## Инфраструктура
- Gateway: system unit `openclaw-gateway`, `/root/openclaw`, `127.0.0.1:18789`.
- Hub: `r2d2-hub`, `/root/atlas-green-pearl-dawn/.output/server/index.mjs`, `127.0.0.1:8091`, `https://hub.gbkz.uk`, `/healthz`, `/readyz`.
- Telegram user service: `127.0.0.1:8765`. Mini App мёртв, `:8080` не слушает.
- Оператор: `@Dmbotmy_bot` → main. Пейджер: `@HubAlertsbot`. Hub agent: `tools.allow=[]`.
- Backup: `/var/backups/r2d2`; watchdog hub и gateway/tgsvc раздельные.

## Гигиена 2026-08-31
- Канон хаба — Node/TanStack Start Nitro, не Python Mini App.
- Дайджест/календарные уведомления не должны иметь параллельные cron-рассылки.
- Git без совпадающего `origin/main` не означает выполненную работу.
- Runtime state, sessions и личные отчёты не коммитить.

## Guardrails
- `openclaw.json` и credentials не править руками; только `openclaw config set` + validate по прямому ТЗ.
- Не менять ufw, zram, bind gateway или `tools.allow=[]` hub без прямого ТЗ.

## TZ-CLOSEOUT 2026-08-31
TZ-CLOSEOUT 2026-08-31 закрыт, отчёт docs/TZ-CLOSEOUT-2026-08-31.md.

## TZ-CANON 2026-09-01
TZ-CANON закрыт, отчёт docs/TZ-CANON-2026-09-01.md.

## TZ-PROOF 2026-09-01
В работе. Live snapshots + restore-drill + optional hub release.
Закрытие = docs/TZ-PROOF-2026-09-01.md на origin.

## Не сейчас (отдельное ТЗ, не делать самовольно)
1. PGLite → PostgreSQL: только после isolated dump/restore/rollback.
2. SecretRefs: только после inventory имён секретов и плана ротации.
3. CalDAV/iCloud: не DROP hub_icloud, пока Google parity и backup не доказаны.
4. Карта Better Auth / migrations/auth до любого удаления зависимости.
5. Снос .vercel/output только после подтверждённого релиз-цикла живого .output.
