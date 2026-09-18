#!/usr/bin/env python3
"""Safe local Oura -> evidence packet pipeline.

Only the sync stage talks to Oura (GET + OAuth refresh). Raw data stays in the
local SQLite database. The packet emitted for an analyst contains aggregate
signals and quality metadata only; MCP/Kimi analysis is deliberately a
separate, read-only stage.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
SCRIPTS = BASE / "scripts"
ANALYSIS = BASE / "analysis"
PACKET = ANALYSIS / "health_evidence_packet.json"


def run(name: str, *args: str) -> dict:
    p = subprocess.run([sys.executable, str(SCRIPTS / name), *args],
                       cwd=BASE, text=True, capture_output=True, timeout=1800)
    if p.returncode:
        raise RuntimeError(f"{name} failed: {p.stderr[-500:]}")
    try:
        return json.loads(p.stdout)
    except json.JSONDecodeError:
        return {"ok": True, "output": p.stdout[-1000:]}


def make_packet() -> dict:
    src = json.loads((ANALYSIS / "current.json").read_text(encoding="utf-8"))
    signals = src.get("signals", {})
    canonical = signals.get("canonical_metrics", {})
    metrics = signals.get("metrics", {})

    # Explicit allow-list: never copy raw, recent daily values, identifiers or
    # arbitrary endpoint payloads into the model/MCP packet.
    names = {"hrv", "rhr", "sleep_score", "readiness", "activity_score",
             "steps", "temp_dev", "spo2", "breathing", "sleep_duration",
             "deep_sleep", "rem_sleep", "nap_duration", "workouts"}
    aggregate = {}
    for name in names:
        if name in metrics:
            item = metrics[name]
            aggregate[name] = {k: item[k] for k in (
                "n", "median", "last", "z_last", "robust_z_last",
                "slope_30d", "reliability"
            ) if k in item}

    packet = {
        "schema": "health-evidence-input.v1",
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "source": "oura",
        "source_mode": "local_aggregate",
        "period": src.get("raw", {}).get("days", {}),
        "data_quality": src.get("quality", {}),
        "metrics": aggregate,
        "anomalies": [
            {k: item[k] for k in ("metric", "status", "severity", "confidence") if k in item}
            for item in signals.get("anomalies", []) if isinstance(item, dict)
        ],
        "patterns": [
            {k: item[k] for k in ("driver", "target", "direction", "n", "effect_size", "confidence") if k in item}
            for item in signals.get("patterns", []) if isinstance(item, dict)
        ],
        "medical_context_request": {
            "query": "wearable sleep quality duration HRV resting heart rate recovery evidence",
            "mode": "read_only",
            "patient_specific": False,
        },
        "safety": {
            "raw_data_included": False,
            "personal_identifiers_included": False,
            "medical_advice": False,
            "diagnosis_allowed": False,
            "causality_allowed": False,
        },
    }
    ANALYSIS.mkdir(exist_ok=True)
    PACKET.write_text(json.dumps(packet, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"written": str(PACKET), "metrics": len(aggregate), "raw_included": False}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=30)
    ap.add_argument("--reports", action="store_true")
    args = ap.parse_args()
    result = {"ok": False, "stages": []}
    try:
        result["stages"].append({"sync": run("oura_sync.py", "--days", str(args.days))})
        result["stages"].append({"analytics": run("analytics.py")})
        result["stages"].append({"packet": make_packet()})
        if args.reports:
            result["stages"].append({"morning": run("morning_report.py")})
            result["stages"].append({"weekly": run("weekly_report.py", "--scope", "weekly")})
        result["ok"] = True
    except Exception as exc:
        result["error"] = type(exc).__name__ + ": " + str(exc)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
