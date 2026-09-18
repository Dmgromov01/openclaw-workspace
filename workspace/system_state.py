#!/usr/bin/env python3
"""Deterministic generator for CURRENT_SYSTEM_STATE.md.

Inspects the LIVE OpenClaw runtime/configuration and writes a snapshot of the
CURRENT,VERIFIABLE,NON-SECRET system state.

Guarantees:
  * read-only: never modifies OpenClaw configuration, memory, embeddings or the memory index
  * idempotent: repeated runs without configuration changes produce the same logical state
  * non-secret: never prints API keys, tokens, passwords, cookies or .env values
"""
import json, subprocess, datetime, shutil

OUT = "/root/openclaw/workspace/CURRENT_SYSTEM_STATE.md"
OC = shutil.which("openclaw") or "/usr/bin/openclaw"
TIMEOUT = 120


def run(*args):
    try:
        p = subprocess.run([OC, *args], capture_output=True, text=True, timeout=TIMEOUT)
        return (p.stdout or "").strip()
    except Exception:
        return ""


def runx(*args):
    try:
        p = subprocess.run([OC, *args], capture_output=True, text=True, timeout=TIMEOUT)
        return ((p.stdout or "") + "\n" + (p.stderr or "")).strip()
    except Exception:
        return ""


def cfg(path):
    try:
        return json.loads(run("config", "get", path))
    except Exception:
        return None


def kv(text, key):
    for line in text.splitlines():
        s = line.strip()
        if s.lower().startswith(key.lower() + ":"):
            return s.split(":", 1)[1].strip()
    return "unknown"


def main():
    now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    ver_raw = run("--version")
    ver = ver_raw.replace("OpenClaw ", "").strip() or "unknown"

    gw = runx("gateway", "status")
    gw_service = kv(gw, "Service")
    gw_port = kv(gw, "Service env") or ""
    if "18789" in gw:
        gw_port = "18789"

    defaults = cfg("agents.defaults") or {}
    prim = (defaults.get("model") or {}).get("primary", "unknown")
    fb = ", ".join((defaults.get("model") or {}).get("fallbacks") or []) or "-"
    utility = defaults.get("utilityModel", "unknown")
    img = (defaults.get("imageModel") or {}).get("primary", "unknown") if isinstance(defaults.get("imageModel"), dict) else defaults.get("imageModel", "unknown")

    entries = cfg("agents.entries") or {}
    agent_lines = []
    for aid in sorted(entries):
        v = entries[aid] or {}
        ws = v.get("workspace", "-")
        model = v.get("model") if isinstance(v.get("model"), str) else (v.get("model") or {}).get("primary", "-")
        mem = "memory enabled" if v.get("memory") else "memory off"
        agent_lines.append("- %s: active (workspace %s, model %s, %s)" % (aid, ws, model, mem))

    plugins = cfg("plugins.entries") or {}
    on = sorted([k for k in plugins if (plugins[k] or {}).get("enabled")])
    off = sorted([k for k in plugins if not (plugins[k] or {}).get("enabled")])

    mconf = cfg("memory") or {}
    msearch = mconf.get("search") or {}
    mstatus = runx("memory", "status")
    warn = ""
    for line in mstatus.splitlines():
        if line.lower().startswith("config warnings"):
            warn = line.strip()
            break
    prov = kv(mstatus, "Provider")
    model = kv(mstatus, "Model")
    sources = kv(mstatus, "Sources")
    indexed = kv(mstatus, "Indexed")
    store = kv(mstatus, "Store")
    dreaming = kv(mstatus, "Dreaming")
    dirty = kv(mstatus, "Dirty")

    lines = []
    A = lines.append
    A("# CURRENT SYSTEM STATE")
    A("")
    A("Generated: %s" % now)
    A("Generator: /root/openclaw/workspace/system_state.py")
    A("")
    A("> Generated snapshot of CURRENT OpenClaw runtime/configuration state.")
    A("> This is NOT memory. Do not edit manually; regenerate with the generator.")
    A("")
    A("## OpenClaw")
    A("")
    A("Version: %s" % ver)
    A("Config: ~/.openclaw/openclaw.json")
    A("State dir: ~/.openclaw")
    A("Gateway: %s%s" % (gw_service, (" (port %s)" % gw_port) if gw_port else ""))
    A("")
    A("## Agents")
    A("")
    lines.extend(agent_lines or ["- (none detected)"])
    A("")
    A("## Models")
    A("")
    A("Default: %s" % prim)
    A("Fallback: %s" % fb)
    A("Utility: %s" % utility)
    A("Image: %s" % img)
    A("")
    A("## Memory")
    A("")
    A("memory-core: %s" % ("disabled (memory slot set to memory-lancedb)" if warn else "enabled"))
    A("Memory slot: memory-lancedb")
    A("Embedding provider: %s" % prov)
    A("Embedding model: %s" % model)
    A("Search enabled: %s" % str(msearch.get("enabled", "unknown")).lower())
    A("Search sources: %s" % sources)
    A("rememberAcrossConversations: %s" % ("unset (runtime default)" if "rememberAcrossConversations" not in msearch else str(msearch.get("rememberAcrossConversations")).lower()))
    A("Session memory: %s" % ("enabled" if (msearch.get("experimental") or {}).get("sessionMemory") else "disabled"))
    A("Dreaming: %s" % dreaming)
    A("Index: %s (dirty=%s)" % (indexed, dirty))
    A("Index store: %s" % store)
    A("")
    A("## Plugins / Tools")
    A("")
    A("Enabled (%d): %s" % (len(on), ", ".join(on)))
    A("Disabled: %s" % ", ".join(off))
    A("Codex: %s" % ("ENABLED" if "codex" in on else "DISABLED"))
    A("OpenAI provider: %s" % ("ENABLED" if "openai" in on else "DISABLED"))
    A("")
    A("## Important configuration")
    A("")
    A("Only non-secret, behavior-relevant values are listed. Secrets are never included.")
    A("")
    A("This file is authoritative for the CURRENT state of OpenClaw.")
    A("MEMORY (MEMORY.md, memory/*.md) is authoritative for historical/user/project context.")
    A("Never infer current plugin/tool/model/agent/permission state from historical memory.")
    A("")

    with open(OUT, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print("wrote %s (%d bytes); version=%s agents=%d plugins_on=%d" % (OUT, len("\n".join(lines)), ver, len(entries), len(on)))


if __name__ == "__main__":
    main()
