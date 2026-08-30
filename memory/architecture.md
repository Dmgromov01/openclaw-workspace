# Architecture — runtime topology and guardrails

> Текущие факты инфраструктуры ведутся в [`STATE.md`](../STATE.md). Этот файл описывает устойчивую топологию, а не исторические хосты, токены или временные обходы.

## Topology
- OpenClaw gateway: systemd `openclaw-gateway`, `/root/openclaw`, `127.0.0.1:18789`; внешний WSS проходит через nginx `gbkz.uk`.
- Hub: systemd `r2d2-hub`, Nitro `/root/atlas-green-pearl-dawn/.output/server/index.mjs`, `127.0.0.1:8091`; внешний доступ только через nginx `hub.gbkz.uk`.
- Telegram user service: systemd `telegram-user-svc`, `127.0.0.1:8765`.
- Mini App отключён; `:8080` не является активным сервисом.

## Data and integrations
- Calendar: Google Calendar user OAuth. Agent CLI supports read and `add`; hub has отдельный Google flow. iCloud в hub — legacy-код до отдельной миграции, не рабочий канон.
- Memory: builtin memory search uses Jina `jina-embeddings-v3` via OpenAI-compatible adapter, only `memory` source, no sessionMemory.
- Secrets live outside git under protected runtime paths. Git remotes must never embed credentials.

## Guardrails
- Config is changed only through `openclaw config set`, then validated; never edit `openclaw.json` or credentials manually.
- Production release requires an explicit approval after branch review, tests, and backup.
- Do not run a second gateway on this host or recreate a user gateway service.
- Use HTTP/cURL/urllib first; browser automation only for JS-required or blocked pages.
- Do not re-enable Google for LLM/vision/fallback. DeepSeek handles chat/vision; Google remains calendar only.
