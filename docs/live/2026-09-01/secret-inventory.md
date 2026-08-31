# Secret inventory — names, paths, modes only

| name | path | mode | gitignored | in_backup_tar |
|---|---|---|---|---|
| nginx ssl directory | /etc/nginx/ssl | absent | runtime config | no |

Backup rule: openclaw-state excludes .env and credentials.
