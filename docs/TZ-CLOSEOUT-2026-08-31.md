# TZ-CLOSEOUT 2026-08-31

## Baseline
workspace: 294d412432b3b71bbb47c4c68fa233df7535df4d
hub:       10804fd629eccec572bcadacefa69d2f1466f087

## Origin after
workspace: f240c37db79a207eb792d66fb40ae1b32dc10a81 https://github.com/Dmgromov01/openclaw-workspace/commit/f240c37db79a207eb792d66fb40ae1b32dc10a81
hub:       820a0080fe7dac96a4c4b0ca843c35da272eb414 https://github.com/Dmgromov01/atlas-green-pearl-dawn/commit/820a0080fe7dac96a4c4b0ca843c35da272eb414

## Health
https://hub.gbkz.uk/healthz  200 {"status":"ok"}
https://hub.gbkz.uk/readyz   200 {"status":"ready","checks":{"database":true,"gateway":true}}

## Steps
| step | path | action | commit sha | proof command output |
|------|------|--------|------------|----------------------|
| S0 | STATE.md | exact closeout in-progress paragraph appended | e16f2116c58daa9f46cb0ae5b4805125d147a876 | origin/main=e16f2116c58daa9f46cb0ae5b4805125d147a876 |
| S1 | docs/bot-blueprint/ | git mv to docs/archive/ | 544be14e7abf6e612ba2412ff78e45af4784d09c | git ls-files docs/bot-blueprint: empty |
| S1 | docs/context7-ref.md | git mv to docs/archive/ | 544be14e7abf6e612ba2412ff78e45af4784d09c | git ls-files docs/context7-ref.md: empty |
| S1 | docs/archive/README.md | rewritten | 544be14e7abf6e612ba2412ff78e45af4784d09c | wc -l: 13 docs/archive/README.md |
| S2 | calendar/tg_sender.py | git mv to archive/2026-08-31/calendar/ | 76202ca6260d50821d50c173652c7ebfd2e4ebf9 | git ls-files calendar/tg_sender.py: empty; crontab: NO_SENDER_CRON |
| S2 | calendar/ics_generator.py | git mv to archive/2026-08-31/calendar/ | 76202ca6260d50821d50c173652c7ebfd2e4ebf9 | git ls-files calendar/ics_generator.py: empty; crontab: NO_SENDER_CRON |
| S2 | calendar/bot_sender.py | KEEP | 76202ca6260d50821d50c173652c7ebfd2e4ebf9 | calendar/bot_sender.py |
| S3 | hub/AGENTS.md | restored to git | f240c37db79a207eb792d66fb40ae1b32dc10a81 | hub/AGENTS.md |
| S3 | hub/SOUL.md | restored to git | f240c37db79a207eb792d66fb40ae1b32dc10a81 | hub/SOUL.md |
| S3 | hub/IDENTITY.md | restored to git | f240c37db79a207eb792d66fb40ae1b32dc10a81 | hub/IDENTITY.md |
| S3 | hub/USER.md | restored to git | f240c37db79a207eb792d66fb40ae1b32dc10a81 | hub/USER.md |
| S3 | hub/TOOLS.md | restored to git | f240c37db79a207eb792d66fb40ae1b32dc10a81 | hub/TOOLS.md |
| S3 | hub/BOOTSTRAP.md | restored to git | f240c37db79a207eb792d66fb40ae1b32dc10a81 | hub/BOOTSTRAP.md |
| S3 | hub/HEARTBEAT.md | restored to git | f240c37db79a207eb792d66fb40ae1b32dc10a81 | hub/HEARTBEAT.md |
| S3 | .gitignore /hub/ | removed, runtime-only ignores | f240c37db79a207eb792d66fb40ae1b32dc10a81 | /hub/**/*.json; /hub/**/*.jsonl; /hub/memory/; /hub/*.session* |
| S4 | hub .grok/* | gitignore + --cached | 74008899c5e4ab92ec97de3bbe9c79415898f165 | git ls-files .grok: empty |
| S5 | package.json test | drop app-data.test.ts | 820a0080fe7dac96a4c4b0ca843c35da272eb414 | scripts tests and specified four TypeScript test files only |
| S6 | docs/TZ-CLOSEOUT-2026-08-31.md | report created | pending commit | raw proofs in this file |
| S7 | origin/main | self-check pending after S6 push | pending commit | commands run after S6 push |

## Negative checks (raw output)

- [x] git ls-files hub/*.md
  hub/AGENTS.md; hub/BOOTSTRAP.md; hub/HEARTBEAT.md; hub/IDENTITY.md; hub/SOUL.md; hub/TOOLS.md; hub/USER.md
- [x] git ls-files docs/bot-blueprint
  empty
- [x] git ls-files docs/context7-ref.md
  empty
- [x] git ls-files calendar/tg_sender.py
  empty
- [x] git ls-files calendar/ics_generator.py
  empty
- [x] git ls-files calendar/bot_sender.py
  calendar/bot_sender.py
- [x] git -C /root/atlas-green-pearl-dawn ls-files .grok
  empty
- [x] grep app-data.test.ts /root/atlas-green-pearl-dawn/package.json
  empty
- [x] grep -Fx '/hub/' /root/openclaw/.gitignore
  empty
- [x] grep runtime hub ignores /root/openclaw/.gitignore
  55:/hub/**/*.json; 56:/hub/**/*.jsonl; 57:/hub/memory/; 58:/hub/*.session*
- [x] healthz 200, readyz 200
  {"status":"ok"} HTTP=200
  {"status":"ready","checks":{"database":true,"gateway":true}} HTTP=200
- [x] this run: no nginx, no systemctl, no crontab edit, no npm run build

## Explicitly NOT done
nginx, ufw, PGLite, SecretRefs, product, gateway restart, tools on hub agent.
