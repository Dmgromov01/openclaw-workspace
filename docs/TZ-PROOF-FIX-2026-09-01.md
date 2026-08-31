# TZ-PROOF-FIX 2026-09-01

## Baseline
workspace: 0b441c1bdecd58274210dd110dc41e5f158deaea
hub:       f4de7038bbd0ff7f2fdd08167837915e891c2092

## Origin after
workspace: 704e1745e71fc49897afef6537724796fa2445e3 https://github.com/Dmgromov01/openclaw-workspace/commit/704e1745e71fc49897afef6537724796fa2445e3
hub: unchanged f4de7038

## Fixes
| id | file | before | after | commit |
|----|------|--------|-------|--------|
| F1 | secret-inventory.md | 1 row ssl absent | 9 base paths plus 2 session paths, no values | ecc162d757d54eacdedbb0d2095de32c01a867b4 |
| F2 | health.txt | healthz 000 | 4 codes lb+public, all 200 | 0046dd7199dcc4b3c2adbf7ceac0850ad6aee1cc |
| F3 | unit-diff.txt | DIFF=YES | DIFF=NO | 704e1745e71fc49897afef6537724796fa2445e3 |

## Health now
utc 2026-08-31T22:48:41Z
loopback_healthz 200
{"status":"ok"}
loopback_readyz 200
{"status":"ready","checks":{"database":true,"gateway":true}}
public_healthz 200
{"status":"ok"}
public_readyz 200
{"status":"ready","checks":{"database":true,"gateway":true}}

## Proof
- secret inventory: 23 lines; 12 metadata rows; values committed=no.
- backup inventory result: openclaw-state archive excludes .env and credentials.
- unit ExecStart git and live: /usr/bin/node /root/atlas-green-pearl-dawn/.output/server/index.mjs.
- hub origin unchanged: f4de7038bbd0ff7f2fdd08167837915e891c2092.
- OFFSITE=no remains fact; no offsite copy was created.

## Negative
- nginx, crontab, systemctl, release, PGLite and product were not changed in this fix.
- docs/live and this report contain no secret values.
