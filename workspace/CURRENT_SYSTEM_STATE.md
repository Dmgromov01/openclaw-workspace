# CURRENT SYSTEM STATE

Generated: 2026-09-16T09:50:59Z
Generator: /root/openclaw/workspace/system_state.py

> Generated snapshot of CURRENT OpenClaw runtime/configuration state.
> This is NOT memory. Do not edit manually; regenerate with the generator.

## OpenClaw

Version: 2026.9.4 (3a9d69d)
Config: ~/.openclaw/openclaw.json
State dir: ~/.openclaw
Gateway: systemd user (enabled) (port 18789)

## Agents

- chat: active (workspace /root/openclaw/workspace-chat, model deepseek/deepseek-v4-flash, memory off)
- groups: active (workspace /root/openclaw/workspace-groups, model deepseek/deepseek-v4-flash, memory off)
- health: active (workspace /root/openclaw/workspace/health, model deepseek/deepseek-flash, memory off)
- main: active (workspace /root/openclaw, model deepseek/deepseek-flash, memory enabled)

## Models

Default: relaymodels/deepseek-v4.1-flash
Fallback: deepseek/deepseek-flash
Utility: relaymodels/kimi-k2.7-code
Image: deepseek/deepseek-flash

## Memory

memory-core: disabled (memory slot set to memory-lancedb)
Memory slot: memory-lancedb
Embedding provider: openrouter (requested: openrouter)
Embedding model: openai/text-embedding-3-small
Search enabled: true
Search sources: memory, sessions
rememberAcrossConversations: unset (runtime default)
Session memory: disabled
Dreaming: light=0 3 * * * · limit=100 · lookbackDays=2 · rem=0 3 * * * · limit=10 · lookbackDays=7 · minPatternStrength=0.75 · deep=0 3 * * * · limit=10 · minScore=0.75 · minRecallCount=3 · minUniqueQueries=3 · recencyHalfLifeDays=14 · maxAgeDays=30 · maxPromotedSnippetTokens=160
Index: 75/75 files · 2037 chunks (dirty=yes)
Index store: ~/.openclaw/agents/main/agent/openclaw-agent.sqlite

## Plugins / Tools

Enabled (19): active-memory, agent-effectiveness, bot-access-command, browser, composio, deepseek, device-pair, diffs, expedia-openclaw, jina-tools, memory-core, memory-lancedb, openai, openrouter, parallel, searxng, tg-user-tools, tokenjuice, workboard
Disabled: codex, google, perplexity, reef, telegram
Codex: DISABLED
OpenAI provider: ENABLED

## Important configuration

Only non-secret, behavior-relevant values are listed. Secrets are never included.

This file is authoritative for the CURRENT state of OpenClaw.
MEMORY (MEMORY.md, memory/*.md) is authoritative for historical/user/project context.
Never infer current plugin/tool/model/agent/permission state from historical memory.
