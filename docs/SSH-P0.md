# P0 на hiplet — только SSH

Этого нет в git. Пока шаги не сделаны, календарь агента и builtin memory search остаются сломаны независимо от merge.

## 1. Builtin memory search ≠ OpenAI default

```bash
openclaw config get agents.defaults.memorySearch
openclaw config get memory.search
```

Ожидание: `jina-embeddings-v3` через `https://api.jina.ai/v1`, provider `openai-compatible`.
Если там `openai` / `text-embedding-3-small` — это дефолт OpenClaw, не хвост ключа. Выставить явно, затем:

```bash
openclaw memory index --force
```

Плагин `jina-tools` builtin search не подменяет.

## 2. Что реально exec’ит хаб

```bash
systemctl cat r2d2-hub | sed -n '/ExecStart/,+2p'
curl -sS -o /dev/null -w '%{http_code}\n' http://127.0.0.1:8091/
```

Должно быть Nitro `.output/server/index.mjs`, не `.vercel/output`. 8091 не в ufw WAN.

## 3. Google OAuth Testing → Production

В Google Cloud Console: OAuth consent screen → Publish app.
Потом новый consent (`prompt=consent&access_type=offline`), обновить `/root/.openclaw/credentials/gcal/tokens.json`.
Пока приложение в Testing, refresh живёт ~7 дней. То же относится к `GOOGLE_CALENDAR_REFRESH_TOKEN` хаба.

Проверка агента:

```bash
python3 /root/openclaw/calendar/gcal_reader.py today
```
