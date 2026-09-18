Skills (56/95 ready)
┌───────────────┬───────────────────────────────────────┬─────────────────────────────────────────┬────────────────────┐
│ Status        │ Skill                                 │ Description                             │ Source             │
├───────────────┼───────────────────────────────────────┼─────────────────────────────────────────┼────────────────────┤
│ disabled      │ 🔐 1password                          │ Set up and use 1Password CLI for sign-  │ openclaw-bundled   │
│               │                                       │ in, desktop integration, and reading    │                    │
│               │                                       │ or injecting secrets.                   │                    │
│ ✓ ready       │ add-model-provider                    │ Add and live-prove a model provider     │ openclaw-custodian │
│               │                                       │ with non-interactive config one-        │                    │
│               │                                       │ liners, without exposing credentials.   │                    │
│ ✓ ready       │ agent-host-runtime-changes            │ Host runtime/policy changes on the      │ openclaw-workshop  │
│               │                                       │ agent's own machine: stage beside,      │                    │
│               │                                       │ rollback, operator handoff.             │                    │
│ △ needs setup │ 📝 apple-notes                        │ Create, view, edit, delete, search,     │ openclaw-bundled   │
│               │                                       │ move, or export Apple Notes via the     │                    │
│               │                                       │ memo CLI on macOS.                      │                    │
│ △ needs setup │ ⏰ apple-reminders                    │ List, add, edit, complete, or delete    │ openclaw-bundled   │
│               │                                       │ Apple Reminders and reminder lists via  │                    │
│               │                                       │ remindctl.                              │                    │
│ △ needs setup │ 🐻 bear-notes                         │ Create, search, and manage Bear notes   │ openclaw-bundled   │
│               │                                       │ via grizzly CLI.                        │                    │
│ disabled      │ 📰 blogwatcher                        │ Monitor blogs and RSS/Atom feeds for    │ openclaw-bundled   │
│               │                                       │ updates using the blogwatcher CLI.      │                    │
│ disabled      │ 🫐 blucli                             │ BluOS CLI (blu) for discovery,          │ openclaw-bundled   │
│               │                                       │ playback, grouping, and volume.         │                    │
│ ✓ ready       │ bot-access-control                    │ Управление доступом Telegram-           │ openclaw-workspace │
│               │                                       │ пользователя OpenClaw только для        │                    │
│               │                                       │ владельца 1916536646 через              │                    │
│               │                                       │ фиксированный оператор.                 │                    │
│ ✓ ready       │ browser-automation                    │ Use when controlling web pages with     │ openclaw-extra     │
│               │                                       │ the OpenClaw browser tool, especially   │                    │
│               │                                       │ multi-step flows, login checks, tab     │                    │
│               │                                       │ management, or recovery from stale      │                    │
│               │                                       │ refs/timeouts.                          │                    │
│ ✓ ready       │ bullmq-queue-semantics                │ Name BullMQ queues, keep the prefix     │ openclaw-workshop  │
│               │                                       │ consistent across Queue/Worker/         │                    │
│               │                                       │ QueueEvents, and prove the namespace    │                    │
│               │                                       │ plus a started worker on a live broker. │                    │
│ ✓ ready       │ 📅 caldav-calendar                    │ Sync and query CalDAV calendars         │ openclaw-workspace │
│               │                                       │ (iCloud, Google, Fastmail, Nextcloud,   │                    │
│               │                                       │ etc.) using vdirsyncer + khal. Works    │                    │
│               │                                       │ on Linux.                               │                    │
│ disabled      │ 📸 camsnap                            │ Capture frames or clips from RTSP/      │ openclaw-bundled   │
│               │                                       │ ONVIF cameras and local webcams,        │                    │
│               │                                       │ including USB pan/tilt/zoom control.    │                    │
│ ✓ ready       │ clawhub                               │ Search ClawHub for skills when a        │ openclaw-bundled   │
│               │                                       │ requested capability is not already     │                    │
│               │                                       │ available; install, verify, update,     │                    │
│               │                                       │ uninstall, publish, or sync skills.     │                    │
│ ✓ ready       │ cloud-image-bake                      │ Bake, select, prove, and safely retire  │ openclaw-custodian │
│               │                                       │ a Cloud Worker image with crabbox and   │                    │
│               │                                       │ config one-liners.                      │                    │
│ ✓ ready       │ codex-harness-openai-binding          │ Put openai/* turns on the Codex         │ openclaw-workshop  │
│               │                                       │ harness with an API-key profile and     │                    │
│               │                                       │ verify them.                            │                    │
│ disabled      │ 🧩 coding-agent                       │ Delegate coding work to Codex, Claude   │ openclaw-bundled   │
│               │                                       │ Code, or OpenCode as background         │                    │
│               │                                       │ workers; not simple edits or read-only  │                    │
│               │                                       │ code lookup.                            │                    │
│ ✓ ready       │ 🔌 composio                           │ Read from or act on external apps       │ openclaw-extra     │
│               │                                       │ (email, calendar, chat, source          │                    │
│               │                                       │ control, tickets, CRM, storage)         │                    │
│               │                                       │ through the Composio CLI, even when     │                    │
│               │                                       │ the user does not name Composio. Not    │                    │
│               │                                       │ for local files, shell, browser, or     │                    │
│               │                                       │ public web search.                      │                    │
│ ✓ ready       │ configure-channel                     │ Configure and prove a chat channel      │ openclaw-custodian │
│               │                                       │ with non-interactive one-liners;        │                    │
│               │                                       │ secrets only as SecretRefs.             │                    │
│ ✓ ready       │ control-ui                            │ Operate and troubleshoot the OpenClaw   │ openclaw-bundled   │
│               │                                       │ Control UI: navigate connected          │                    │
│               │                                       │ clients, organize sessions, build       │                    │
│               │                                       │ session dashboards, and handle direct   │                    │
│               │                                       │ or Tailscale-hosted Gateways.           │                    │
│ ✓ ready       │ diagnose-gateway                      │ Diagnose Gateway, config, secrets,      │ openclaw-custodian │
│               │                                       │ channels, and port failures with read-  │                    │
│               │                                       │ only one-liners.                        │                    │
│ ✓ ready       │ 🧭 diagram-maker                      │ Create SVG/HTML or Excalidraw diagrams  │ openclaw-bundled   │
│               │                                       │ for concepts, architecture, flows, and  │                    │
│               │                                       │ whiteboards.                            │                    │
│ ✓ ready       │ diffs                                 │ Use the diffs tool to produce real,     │ openclaw-extra     │
│               │                                       │ shareable diffs (viewer URL, file       │                    │
│               │                                       │ artifact, or both) instead of manual    │                    │
│               │                                       │ edit summaries.                         │                    │
│ ✓ ready       │ docker-compose-service-bringup        │ Bring up Compose services when a build  │ openclaw-workshop  │
│               │                                       │ or healthcheck fails, verify them, and  │                    │
│               │                                       │ give a host-side app or test access     │                    │
│               │                                       │ when the Compose file publishes no      │                    │
│               │                                       │ ports.                                  │                    │
│ ✓ ready       │ drizzle-kit-migrations                │ Apply or generate Drizzle ORM           │ openclaw-workshop  │
│               │                                       │ migrations for a Postgres app, and      │                    │
│               │                                       │ diagnose a migrate that reports         │                    │
│               │                                       │ success while changing nothing.         │                    │
│ disabled      │ 🛌 eightctl                           │ Control Eight Sleep pods (status,       │ openclaw-bundled   │
│               │                                       │ temperature, alarms, schedules).        │                    │
│ ✓ ready       │ external-cli-exec-blocker             │ Check and recover external-app CLI      │ openclaw-workshop  │
│               │                                       │ access under exec allowlists without    │                    │
│               │                                       │ bypassing policy.                       │                    │
│ ✓ ready       │ flights                               │ Search for cheap flights and airfare    │ openclaw-workspace │
│               │                                       │ via Travelpayouts/Aviasales API.        │                    │
│               │                                       │ Supports date-specific search, price    │                    │
│               │                                       │ calendar, round-trip, cheapest-price    │                    │
│               │                                       │ monitoring, popular destinations, and   │                    │
│               │                                       │ IATA code lookup. Use when user asks    │                    │
│               │                                       │ to find flights, airfare, cheap         │                    │
│               │                                       │ tickets, plane tickets, or says         │                    │
│               │                                       │ phrases like "find flights", "fly to",  │                    │
│               │                                       │ "book a ticket", "авиабилеты",          │                    │
│               │                                       │ "перелёт", "найди билеты", "дешёвые     │                    │
│               │                                       │ билеты", "купить билет".                │                    │
│ disabled      │ ✨ gemini                             │ Gemini CLI one-shot prompts,            │ openclaw-bundled   │
│               │                                       │ summaries, generation, skills, hooks,   │                    │
│               │                                       │ MCP, or Gemma routing.                  │                    │
│ disabled      │ gh-issues                             │ Fetch GitHub issues, select             │ openclaw-bundled   │
│               │                                       │ candidates, spawn background fix        │                    │
│               │                                       │ agents, open PRs, and optionally        │                    │
│               │                                       │ process PR review comments.             │                    │
│ disabled      │ 🧲 gifgrep                            │ Search GIF providers with CLI/TUI,      │ openclaw-bundled   │
│               │                                       │ download results, and extract stills/   │                    │
│               │                                       │ sheets.                                 │                    │
│ disabled      │ 🐙 github                             │ GitHub CLI for issues, PRs, CI/check    │ openclaw-bundled   │
│               │                                       │ logs, comments, reviews, releases,      │                    │
│               │                                       │ repos, and gh api queries.              │                    │
│ disabled      │ 🎮 gog                                │ Google Workspace CLI for Gmail,         │ openclaw-bundled   │
│               │                                       │ Calendar, Drive, Contacts, Sheets, and  │                    │
│               │                                       │ Docs.                                   │                    │
│ disabled      │ 📍 goplaces                           │ Query Google Places for text search,    │ openclaw-bundled   │
│               │                                       │ place details, resolve, reviews, or     │                    │
│               │                                       │ scriptable JSON via goplaces.           │                    │
│ ✓ ready       │ healthcheck                           │ Audit/harden OpenClaw hosts: SSH,       │ openclaw-bundled   │
│               │                                       │ firewall, updates, exposure, backups,   │                    │
│               │                                       │ disk encryption, gateway security.      │                    │
│ disabled      │ 📧 himalaya                           │ Himalaya CLI for IMAP/SMTP mail: list,  │ openclaw-bundled   │
│               │                                       │ read, search, compose, reply, forward,  │                    │
│               │                                       │ copy, move, delete.                     │                    │
│ ✓ ready       │ hub-route-preprod-audit               │ Audit a Hub route/page before pre-      │ openclaw-workshop  │
│               │                                       │ prod: exact file/line findings,         │                    │
│               │                                       │ privacy/API/secrets/auth/XSS/a11y       │                    │
│               │                                       │ checks, GO/NO-GO report.                │                    │
│ ✓ ready       │ hub-tanstack-server-data-wiring       │ Wire server-side data into the r2d2     │ openclaw-workshop  │
│               │                                       │ hub (TanStack Start + Nitro) — server   │                    │
│               │                                       │ functions, external APIs, LLM calls.    │                    │
│               │                                       │ Use when adding or debugging data flow  │                    │
│               │                                       │ in the hub app.                         │                    │
│ disabled      │ 📦 mcporter                           │ List, configure, authenticate, call,    │ openclaw-bundled   │
│               │                                       │ and inspect MCP servers/tools with      │                    │
│               │                                       │ mcporter over HTTP or stdio.            │                    │
│ disabled      │ 🖼️ meme-maker                         │ Search meme templates, suggest          │ openclaw-bundled   │
│               │                                       │ formats, and generate local or hosted   │                    │
│               │                                       │ image memes.                            │                    │
│ disabled      │ 📊 model-usage                        │ Summarize CodexBar local cost logs by   │ openclaw-bundled   │
│               │                                       │ model for Codex or Claude, including    │                    │
│               │                                       │ current or full breakdowns.             │                    │
│ △ needs setup │ 📄 nano-pdf                           │ Edit PDFs with natural-language         │ openclaw-bundled   │
│               │                                       │ instructions using the nano-pdf CLI.    │                    │
│ ✓ ready       │ node-connect                          │ Diagnose OpenClaw Control UI browser    │ openclaw-bundled   │
│               │                                       │ and native Android, iOS, or macOS node  │                    │
│               │                                       │ connection failures across route,       │                    │
│               │                                       │ auth, pairing, QR/setup-code, and       │                    │
│               │                                       │ reconnect states.                       │                    │
│ ✓ ready       │ 🪲 node-inspect-debugger              │ Debug Node.js with node inspect, --     │ openclaw-bundled   │
│               │                                       │ inspect, breakpoints, CDP, heap, and    │                    │
│               │                                       │ CPU profiles.                           │                    │
│ disabled      │ 📝 notion                             │ Notion CLI/API for pages, Markdown      │ openclaw-bundled   │
│               │                                       │ content, data sources, files,           │                    │
│               │                                       │ comments, search, Workers, and raw API  │                    │
│               │                                       │ calls.                                  │                    │
│ ✓ ready       │ oauth2-authorization-code-integration │ Diagnose and verify server-side OAuth2  │ openclaw-workshop  │
│               │                                       │ authorization-code integrations,        │                    │
│               │                                       │ including verification under a          │                    │
│               │                                       │ restricted shell.                       │                    │
│ ✓ ready       │ oauth2-token-endpoint-diagnosis       │ Diagnose OAuth2 token-exchange and      │ openclaw-workshop  │
│               │                                       │ refresh failures by probing the live    │                    │
│               │                                       │ endpoint's error signatures before      │                    │
│               │                                       │ editing client code.                    │                    │
│ disabled      │ 💎 obsidian                           │ Work with Obsidian vaults using the     │ openclaw-bundled   │
│               │                                       │ official obsidian CLI: read/search/     │                    │
│               │                                       │ create/edit notes, tasks, links,        │                    │
│               │                                       │ properties, plugins.                    │                    │
│ disabled      │ 🎤 openai-whisper                     │ Local speech-to-text with the Whisper   │ openclaw-bundled   │
│               │                                       │ CLI (no API key).                       │                    │
│ disabled      │ 🌐 openai-whisper-api                 │ OpenAI Audio Transcriptions API via     │ openclaw-bundled   │
│               │                                       │ curl; gpt-4o-transcribe, mini,          │                    │
│               │                                       │ diarize, or whisper-1.                  │                    │
│ ✓ ready       │ openclaw-agent-roster-changes         │ Add, remove or rebind an OpenClaw       │ openclaw-workshop  │
│               │                                       │ agent: back up config, delete via       │                    │
│               │                                       │ `openclaw agents delete` (config unset  │                    │
│               │                                       │ refuses roster drops), check app        │                    │
│               │                                       │ consumers, validate.                    │                    │
│ ✓ ready       │ openclaw-browser-host-setup           │ Launch and verify OpenClaw's managed    │ openclaw-workshop  │
│               │                                       │ browser on a headless Linux host,       │                    │
│               │                                       │ recover Chrome CDP startup failures,    │                    │
│               │                                       │ and choose the right browser profile    │                    │
│               │                                       │ for logins.                             │                    │
│ ✓ ready       │ openclaw-codex-runtime                │ Codex runtime: run OpenAI agent turns   │ openclaw-workshop  │
│               │                                       │ through Codex app-server; confirm       │                    │
│               │                                       │ harness and auth, verify Runtime:       │                    │
│               │                                       │ OpenAI Codex, clear the exec-mode gate. │                    │
│ ✓ ready       │ openclaw-cron-delivery-jobs           │ Create, verify and test an OpenClaw     │ openclaw-workshop  │
│               │                                       │ automation (cron job) that runs a       │                    │
│               │                                       │ scheduled agent turn or command and     │                    │
│               │                                       │ delivers its result to a chat channel.  │                    │
│               │                                       │ Use for any recurring/daily report,     │                    │
│               │                                       │ reminder, or scheduled message request. │                    │
│ ✓ ready       │ openclaw-delegate-model-turn          │ Run a one-off agent turn or delegate a  │ openclaw-workshop  │
│               │                                       │ fix task to a specific provider/model   │                    │
│               │                                       │ via the CLI or a child session,         │                    │
│               │                                       │ including the model-allow-list          │                    │
│               │                                       │ requirement and result collection.      │                    │
│ ✓ ready       │ openclaw-exec-allowlist               │ Diagnose "exec denied: allowlist        │ openclaw-workshop  │
│               │                                       │ miss", manage the exec allowlist via    │                    │
│               │                                       │ the approvals CLI (not openclaw.json),  │                    │
│               │                                       │ and run scripts under the cwd-change    │                    │
│               │                                       │ restriction.                            │                    │
│ ✓ ready       │ openclaw-exec-process-sessions        │ Handle exec results that return a       │ openclaw-workshop  │
│               │                                       │ background process session, and read    │                    │
│               │                                       │ compacted/oversized tool output: poll/  │                    │
│               │                                       │ log via the process tool instead of     │                    │
│               │                                       │ retrying, and chunk file reads that     │                    │
│               │                                       │ arrive with the middle dropped.         │                    │
│ ✓ ready       │ openclaw-exec-recovery                │ Host-exec OpenClaw — gateway-контекст,  │ openclaw-workshop  │
│               │                                       │ пустой allowlist, headless-deny.        │                    │
│ ✓ ready       │ openclaw-gateway-device-pairing       │ Pair a non-browser client to a self-    │ openclaw-workshop  │
│               │                                       │ hosted OpenClaw Gateway WebSocket:      │                    │
│               │                                       │ Ed25519 device identity, connect.       │                    │
│               │                                       │ challenge signing, device token, and    │                    │
│               │                                       │ the hello-ok method/response contract.  │                    │
│ ✓ ready       │ openclaw-host-maintenance             │ Self-hosted headless OpenClaw ops:      │ openclaw-workshop  │
│               │                                       │ core updates, plugin drift, restart     │                    │
│               │                                       │ drain, verified backup windows,         │                    │
│               │                                       │ managed Chrome.                         │                    │
│ ✓ ready       │ openclaw-image-generation-resolution  │ Verify OpenClaw media generation        │ openclaw-workshop  │
│               │                                       │ capability (image/video), pick a        │                    │
│               │                                       │ capable provider, avoid JSON response   │                    │
│               │                                       │ ceilings, and keep identity by          │                    │
│               │                                       │ retouching originals.                   │                    │
│ ✓ ready       │ openclaw-model-catalog-update         │ Add a provider model id missing from    │ openclaw-workshop  │
│               │                                       │ the hosted OpenClaw catalog, switch     │                    │
│               │                                       │ default/vision models and aliases, and  │                    │
│               │                                       │ apply via the reload-mode gate.         │                    │
│ ✓ ready       │ openclaw-model-credentials            │ Diagnose and repair OpenClaw model-     │ openclaw-workshop  │
│               │                                       │ provider credentials — which store      │                    │
│               │                                       │ wins, how to prove it from the          │                    │
│               │                                       │ provider error, and repairs that work   │                    │
│               │                                       │ while the Gateway is running.           │                    │
│ ✓ ready       │ openclaw-model-provider-onboarding    │ Onboard or repair a model provider      │ openclaw-workshop  │
│               │                                       │ credential without leaking the key:     │                    │
│               │                                       │ store the secret, write config,         │                    │
│               │                                       │ confirm which credential is effective,  │                    │
│               │                                       │ prove.                                  │                    │
│ ✓ ready       │ openclaw-model-provider-silent-fix    │ Diagnose and fix an OpenClaw model      │ openclaw-workshop  │
│               │                                       │ provider that stops responding.         │                    │
│               │                                       │ Distinguish a missing key from stale    │                    │
│               │                                       │ model IDs, then repair via openclaw     │                    │
│               │                                       │ config set --replace.                   │                    │
│ ✓ ready       │ openclaw-model-provider-triage        │ Retired: diagnose a configured-but-     │ openclaw-workshop  │
│               │                                       │ silent OpenClaw model provider. Use     │                    │
│               │                                       │ openclaw-model-provider-silent-fix      │                    │
│               │                                       │ instead.                                │                    │
│ ✓ ready       │ openclaw-release-check                │ Check installed vs latest OpenClaw      │ openclaw-workshop  │
│               │                                       │ version and update options (версия      │                    │
│               │                                       │ OpenClaw, обновление).                  │                    │
│ ✓ ready       │ openclaw-session-delete               │ Delete one stored OpenClaw              │ openclaw-workshop  │
│               │                                       │ conversation session by exact key via   │                    │
│               │                                       │ the gateway CLI, verify no collateral   │                    │
│               │                                       │ deletion, and handle the archived       │                    │
│               │                                       │ transcript's memory-search residue.     │                    │
│ ✓ ready       │ openclaw-update-triage                │ Diagnose a failed or stuck OpenClaw     │ openclaw-workshop  │
│               │                                       │ update: preview read-only, read the     │                    │
│               │                                       │ failure artifact, clear an abandoned    │                    │
│               │                                       │ update, hand the owner commands.        │                    │
│ ✓ ready       │ openclaw-user-tool-access             │ Grant or revoke tools (web, PDF,        │ openclaw-workshop  │
│               │                                       │ files, image) for a Telegram user       │                    │
│               │                                       │ bound to a restricted OpenClaw agent:   │                    │
│               │                                       │ edit the access operator's ALLOW        │                    │
│               │                                       │ constant, re-apply, verify. Use when    │                    │
│               │                                       │ per-user tool access must change.       │                    │
│ disabled      │ 💡 openhue                            │ Control Philips Hue lights and scenes   │ openclaw-bundled   │
│               │                                       │ via the OpenHue CLI.                    │                    │
│ disabled      │ 🧿 oracle                             │ Oracle CLI second-model review/debug/   │ openclaw-bundled   │
│               │                                       │ refactor/design with selected files,    │                    │
│               │                                       │ dry-run token checks, API or browser    │                    │
│               │                                       │ engine.                                 │                    │
│ disabled      │ 🛵 ordercli                           │ Foodora-only CLI for checking past      │ openclaw-bundled   │
│               │                                       │ orders and active order status          │                    │
│               │                                       │ (Deliveroo WIP).                        │                    │
│ ✓ ready       │ oura-data-sync-maintenance            │ Sync Oura safely and verify live read-  │ openclaw-workshop  │
│               │                                       │ only authorization before analytics;    │                    │
│               │                                       │ keep bounded v2 windows and raw-error   │                    │
│               │                                       │ checks.                                 │                    │
│ △ needs setup │ 👀 peekaboo                           │ Capture and automate macOS UI with the  │ openclaw-bundled   │
│               │                                       │ Peekaboo CLI.                           │                    │
│ ✓ ready       │ privacy-harden-fixture-data           │ Replace real personal values in client  │ openclaw-workshop  │
│               │                                       │ fixtures with synthetic demo data;      │                    │
│               │                                       │ verify tests, executable availability,  │                    │
│               │                                       │ bundle scan, and audit report.          │                    │
│ disabled      │ python-debugpy                        │ Debug Python with pdb, breakpoint(),    │ openclaw-bundled   │
│               │                                       │ post-mortem inspection, and debugpy     │                    │
│               │                                       │ remote attach.                          │                    │
│ ✓ ready       │ r2d2-hub                              │ Семейный хаб hub.gbkz.uk — контракт     │ openclaw-workspace │
│               │                                       │ развёртывания, auth (Face ID/PIN/       │                    │
│               │                                       │ инвайт), чат через gateway, запреты и   │                    │
│               │                                       │ probes.                                 │                    │
│ disabled      │ 🔊 sag                                │ ElevenLabs text-to-speech with mac-     │ openclaw-bundled   │
│               │                                       │ style say UX.                           │                    │
│ disabled      │ 🔉 sherpa-onnx-tts                    │ Local text-to-speech via sherpa-onnx    │ openclaw-bundled   │
│               │                                       │ (offline, no cloud)                     │                    │
│ ✓ ready       │ skill-creator                         │ Author or review AgentSkills: create,   │ openclaw-bundled   │
│               │                                       │ repair, validate, or restructure SKILL. │                    │
│               │                                       │ md files and bundled resources.         │                    │
│ disabled      │ 🌊 songsee                            │ Generate spectrograms and feature-      │ openclaw-bundled   │
│               │                                       │ panel visualizations from audio with    │                    │
│               │                                       │ the songsee CLI.                        │                    │
│ disabled      │ 🔊 sonoscli                           │ Control Sonos speakers (discover/       │ openclaw-bundled   │
│               │                                       │ status/play/volume/group).              │                    │
│ disabled      │ 🧪 spike                              │ Run throwaway prototypes to validate    │ openclaw-bundled   │
│               │                                       │ feasibility, compare approaches, and    │                    │
│               │                                       │ report a verdict.                       │                    │
│ disabled      │ 🎵 spotify-player                     │ Terminal Spotify playback/search via    │ openclaw-bundled   │
│               │                                       │ spogo (preferred) or spotify_player.    │                    │
│ ✓ ready       │ subdomain-public-reachability         │ Diagnose a new subdomain or hostname    │ openclaw-workshop  │
│               │                                       │ that «doesn't come up»: separate DNS,   │                    │
│               │                                       │ TLS, nginx and process layers, then     │                    │
│               │                                       │ name the missing one.                   │                    │
│ disabled      │ 🧾 summarize                          │ Summarize or transcribe URLs, YouTube/  │ openclaw-bundled   │
│               │                                       │ videos, podcasts, articles,             │                    │
│               │                                       │ transcripts, PDFs, and local files.     │                    │
│ ✓ ready       │ 🪝 taskflow                           │ Run approval-gated workflows with       │ openclaw-bundled   │
│               │                                       │ durable TaskFlow state; distinguish     │                    │
│               │                                       │ workflow execution from linking real    │                    │
│               │                                       │ detached tasks.                         │                    │
│ ✓ ready       │ 📥 taskflow-inbox-triage              │ Preview synthetic inbox routing with a  │ openclaw-bundled   │
│               │                                       │ real TaskFlow approval pause, and       │                    │
│               │                                       │ identify the adapters needed for live   │                    │
│               │                                       │ triage.                                 │                    │
│ △ needs setup │ ✅ things-mac                         │ Add, update, list, search, or inspect   │ openclaw-bundled   │
│               │                                       │ Things 3 todos, inbox, today,           │                    │
│               │                                       │ projects, areas, and tags on macOS.     │                    │
│ ✓ ready       │ 🧵 tmux                               │ Control tmux sessions/panes for         │ openclaw-bundled   │
│               │                                       │ interactive CLIs: list, capture         │                    │
│               │                                       │ output, send keys, paste text, monitor  │                    │
│               │                                       │ prompts.                                │                    │
│ ✓ ready       │ travel-search                         │ Search live hotel, resort, vacation     │ openclaw-extra     │
│               │                                       │ rental, and flight inventory via the    │                    │
│               │                                       │ EG Travel adapter. Use for any lodging  │                    │
│               │                                       │ or flight query — hotels, vacation      │                    │
│               │                                       │ rentals, accommodations, flights for    │                    │
│               │                                       │ specific dates and routes. Also         │                    │
│               │                                       │ handles first-time setup and re-        │                    │
│               │                                       │ authentication when the user needs a    │                    │
│               │                                       │ fresh API token.                        │                    │
│ disabled      │ 📋 trello                             │ Manage Trello boards, lists, and cards  │ openclaw-bundled   │
│               │                                       │ via the Trello REST API.                │                    │
│ ✓ ready       │ ☔ weather                            │ Current weather and forecasts with web_ │ openclaw-bundled   │
│               │                                       │ fetch, falling back to wttr.in curl     │                    │
│               │                                       │ for locations, rain, temperature,       │                    │
│               │                                       │ travel planning.                        │                    │
│ disabled      │ 🐦 xurl                               │ xurl CLI for authenticated X posts,     │ openclaw-bundled   │
│               │                                       │ replies, reads/search, DMs, media       │                    │
│               │                                       │ upload, followers, auth status, or raw  │                    │
│               │                                       │ v2 API calls.                           │                    │
└───────────────┴───────────────────────────────────────┴─────────────────────────────────────────┴────────────────────┘

Tip: use `openclaw skills search`, `openclaw skills install`, and `openclaw skills update` for ClawHub-backed skills.
