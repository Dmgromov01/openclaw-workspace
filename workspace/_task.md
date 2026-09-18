# OpenClaw Production Memory Reliability Upgrade

You are modifying an existing production OpenClaw installation.

Your task is to improve cross-session reliability of memory and, separately, make current OpenClaw system state explicit.

This is an IN-PLACE upgrade.

The existing system is working and must not be rebuilt.

## PRIMARY OBJECTIVE

Solve this class of problem:

The user changes the current OpenClaw configuration, for example:

* disables a plugin/tool;
* changes a model;
* changes an agent;
* changes permissions;
* changes another system component.

After a new session, the assistant incorrectly reports the old state because historical memory conflicts with the current runtime configuration.

The solution MUST distinguish:

1. historical/user/project memory;
2. current OpenClaw runtime state.

Do not attempt to solve this by replacing the existing memory system.

---

# ABSOLUTE SAFETY RULES

Before making any change:

1. Perform a READ-ONLY audit.
2. Create a backup of every file that will be modified.
3. Never expose secrets.
4. Never print API keys, OAuth tokens, passwords, cookies, or `.env` contents.

DO NOT:

* reinstall OpenClaw;
* reset OpenClaw;
* recreate agents;
* recreate workspaces;
* change agent IDs;
* change routing;
* change channels;
* change model providers;
* change authentication;
* change OpenAI embeddings;
* change embedding models;
* change memory provider;
* replace memory-core;
* replace the SQLite memory index;
* delete MEMORY.md;
* delete memory/*.md;
* migrate memory to another database;
* enable QMD;
* install another memory provider;
* enable session-memory unless it is already enabled;
* modify `rememberAcrossConversations` unless the audit proves it is incorrectly configured;
* run `openclaw memory index --force`;
* run destructive migrations;
* modify unrelated OpenClaw configuration.

Do not optimize anything that is not directly required for this task.

---

# PHASE 1 — READ-ONLY AUDIT

Inspect the existing installation.

Determine:

## OpenClaw

* version
* config path
* state directory
* gateway status

## Agents

For every agent:

* agent ID
* workspace
* active/inactive status
* memory configuration

## Memory

Determine:

* active memory plugin
* memory-core status
* memory search provider
* embedding provider
* embedding model
* memory search sources
* `rememberAcrossConversations`
* memory index location
* whether session memory is enabled
* whether dreaming is enabled
* whether automatic memory flush is enabled

## Files

Locate:

* MEMORY.md
* USER.md if present
* memory/*.md
* AGENTS.md
* relevant plugin configuration

Do not modify anything during this phase.

Create:

/root/openclaw/workspace/memory-audit.json

The file must contain only non-secret metadata.

---

# PHASE 2 — VERIFY EXISTING MEMORY BEFORE CHANGES

Use the existing OpenClaw memory tools/CLI to verify that the current memory system works.

Do NOT rebuild the index.

Run read-only checks equivalent to:

* memory status
* memory search
* targeted memory retrieval

Test at least:

1. a known stable user/project fact;
2. a known OpenClaw architectural decision;
3. the word "Codex".

Record whether the memory system can retrieve the relevant historical information.

IMPORTANT:

Do not treat retrieval of an old Codex-related memory as evidence that Codex is currently enabled.

That distinction is the core purpose of this upgrade.

---

# PHASE 3 — DO NOT CHANGE THE EXISTING MEMORY ARCHITECTURE

The existing memory system remains the authoritative historical/contextual memory.

Keep:

* memory-core;
* OpenAI embeddings;
* existing embedding model;
* existing SQLite index;
* MEMORY.md;
* memory/*.md;
* existing memory search configuration.

Do not create:

* a second vector database;
* a second embedding system;
* a second memory provider;
* a duplicate MEMORY.md;
* a parallel memory retrieval system.

The existing Markdown memory files remain the source of truth for persistent memory.

---

# PHASE 4 — CREATE CURRENT SYSTEM STATE

Create exactly one new file:

/root/openclaw/workspace/CURRENT_SYSTEM_STATE.md

This is NOT memory.

It is a generated snapshot of current OpenClaw runtime/configuration state.

It must contain only current, verifiable infrastructure facts.

Example structure:

# CURRENT SYSTEM STATE

Generated: <timestamp>

## OpenClaw

Version:
Gateway:
Config:

## Agents

main: active
chat: active
groups: active
health: active

## Models

Default:
Fallback:

## Memory

memory-core: enabled
Embedding provider: OpenAI
Embedding model: <model>
rememberAcrossConversations: enabled/disabled
Session memory: enabled/disabled
Dreaming: enabled/disabled

## Plugins / Tools

Only list important currently verified components.

Example:

Codex: DISABLED

## Important configuration

Only list non-secret values relevant to agent behavior.

Never include:

* API keys
* tokens
* passwords
* secrets
* .env values

---

# PHASE 5 — CREATE A DETERMINISTIC GENERATOR

Create:

/root/openclaw/workspace/system_state.py

Its only purpose is to regenerate:

/root/openclaw/workspace/CURRENT_SYSTEM_STATE.md

from the actual OpenClaw runtime/configuration.

The generated file must NOT be manually edited.

The generator must:

1. inspect current OpenClaw state;
2. extract only non-secret operational information;
3. write CURRENT_SYSTEM_STATE.md;
4. never modify OpenClaw configuration;
5. never modify memory;
6. never modify embeddings;
7. never modify the memory index.

The generator must be idempotent.

Running it repeatedly without configuration changes must produce the same logical state.

---

# PHASE 6 — MEMORY VS CURRENT STATE RULE

Add the smallest possible additive instruction to the appropriate existing AGENTS.md.

DO NOT replace the existing AGENTS.md.

DO NOT rewrite existing instructions.

Add rules equivalent to:

CURRENT SYSTEM STATE and runtime configuration are authoritative for the current state of OpenClaw.

MEMORY is authoritative for historical, user, project and previously confirmed contextual information.

Never infer the current state of a plugin, tool, model, agent or permission from historical memory.

When historical memory conflicts with CURRENT_SYSTEM_STATE:

* treat historical memory as historical information;
* treat CURRENT_SYSTEM_STATE as current state.

If the current state cannot be verified, explicitly state that it is unknown.

Never invent current system state.

---

# PHASE 7 — MEMORY WRITING POLICY

Do NOT redesign the existing memory-writing mechanism.

Use the existing OpenClaw memory workflow.

Maintain the following conceptual separation:

MEMORY.md:

* durable facts;
* stable preferences;
* durable project context;
* confirmed decisions;
* concise long-term knowledge.

memory/YYYY-MM-DD.md:

* daily work;
* temporary context;
* session observations;
* detailed working notes.

Do not turn MEMORY.md into a transcript.

Do not copy every conversation into memory.

Keep durable memory concise.

When a user explicitly says "remember this", persist it through the existing memory mechanism.

---

# PHASE 8 — CONFLICT HANDLING

If the user asks:

"Is Codex enabled?"

The assistant must NOT answer from memory.

It must use:

CURRENT_SYSTEM_STATE.md

or verify the actual runtime configuration.

If CURRENT_SYSTEM_STATE says:

Codex: DISABLED

the answer must be:

"Codex is disabled."

Even if memory_search returns historical notes saying that Codex was previously installed or used.

Historical memory may be mentioned only as historical context.

---

# PHASE 9 — DO NOT CREATE DECISIONS.MD YET

Do NOT create:

DECISIONS.md

Do NOT create:

PROJECTS.md

Do NOT create:

CURRENT_CONTEXT.md

Do NOT create:

another memory database.

Do not introduce multiple competing sources of truth.

If later testing proves that a dedicated decision layer is necessary, that will be a separate change.

For this task, keep the architecture minimal.

---

# PHASE 10 — VALIDATION

Before restarting anything, run:

1. memory status;
2. memory search for a known fact;
3. memory search for "Codex";
4. system_state.py;
5. verify CURRENT_SYSTEM_STATE.md;
6. verify existing OpenClaw configuration has not changed;
7. verify embedding provider/model has not changed;
8. verify memory index has not been rebuilt.

Do not restart the Gateway yet.

---

# PHASE 11 — FRESH SESSION TEST

Start a new OpenClaw session using the normal existing mechanism.

Do not manually inject the answer.

Ask:

"What is the current OpenClaw system state?"

Then ask:

"Is Codex currently enabled?"

The answer must reflect CURRENT_SYSTEM_STATE / actual runtime state.

Then ask a historical question that should be answered from memory.

Verify that:

* current state comes from current state;
* historical context comes from memory.

---

# PHASE 12 — RESTART TEST

Only after all previous tests pass:

Restart OpenClaw using the existing production restart mechanism.

Do not change the restart mechanism.

After restart verify:

1. Gateway healthy;
2. agents available;
3. routing works;
4. memory-core works;
5. memory search works;
6. OpenAI embeddings still work;
7. existing memory is still retrievable;
8. CURRENT_SYSTEM_STATE can be regenerated;
9. Codex/current tool state is correctly reported.

---

# PHASE 13 — ROLLBACK

If any existing memory, embedding, agent, routing or model functionality breaks:

STOP.

Do not attempt an automatic repair.

Report:

* exact failure;
* files modified;
* backup location;
* commands required for rollback.

Do not delete data.

---

# PHASE 14 — FINAL REPORT

Return a concise report with:

1. OpenClaw version;
2. current memory provider;
3. current embedding provider/model;
4. whether OpenAI embeddings were modified;
5. whether memory index was modified;
6. whether MEMORY.md was modified;
7. whether memory/*.md was modified;
8. files created;
9. files modified;
10. backup location;
11. current CURRENT_SYSTEM_STATE;
12. memory test result;
13. fresh-session test result;
14. restart test result;
15. any unresolved issue.

IMPORTANT:

Do not claim success unless the existing memory system and OpenAI embedding search have been explicitly verified after the change.

The primary requirement is ZERO REGRESSION of the existing memory system.
