# Secret inventory — names, paths, modes only
Снято: 2026-08-31T22:44:17Z. Значения не читались.

| name | path | exists | mode | gitignored | in_backup_tar |
|------|------|--------|------|------------|---------------|
| hub env | /root/atlas-green-pearl-dawn/.env | yes | 600 | yes | no |
| workspace env | /root/openclaw/.env | no | ABSENT | yes | no |
| openclaw runtime env | /root/.openclaw/.env | yes | 600 | n/a runtime | no |
| gcal oauth client | /root/.openclaw/credentials/gcal/oauth-client.json | yes | 600 | n/a runtime | no |
| gcal tokens | /root/.openclaw/credentials/gcal/tokens.json | yes | 600 | n/a runtime | no |
| tg_bot env | /root/tg_bot/.env | no | ABSENT | n/a runtime | no |
| le fullchain | /etc/letsencrypt/live/hub.gbkz.uk/fullchain.pem | yes | 777 | n/a | no |
| le privkey | /etc/letsencrypt/live/hub.gbkz.uk/privkey.pem | yes | 777 | n/a | no |
| nginx ssl dir | /etc/nginx/ssl | no | ABSENT | n/a | no |

## Sessions (paths and modes only)
| path | mode | gitignored | in_backup_tar |
|------|------|------------|---------------|
| /root/telegram-user-svc/user.session | 644 | n/a runtime | no |
| /root/telegram-user-svc/user_session.session | 644 | n/a runtime | no |

Backup rule: openclaw-state tar excludes .env and credentials; tar list result: EXCLUDED_OR_EMPTY.
Certs = Let's Encrypt, not /etc/nginx/ssl.
