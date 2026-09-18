#!/usr/bin/env python3
"""Trend and pattern reports.

  --scope weekly   (default) 7-day trend and pattern check
  --scope monthly            30-day deep personal analysis

Both compare the current window with the preceding one, surface trends and
repeating patterns, and append newly discovered regularities to
memory/observations.md so the agent can later cite "this is the 7th case".
Writes analysis/weekly.json or analysis/monthly.json. Facts only.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import analytics  # noqa: E402

BASE = Path(__file__).resolve().parents[1]
OBS_PATH = BASE / "memory" / "observations.md"

FOCUS = ("sleep_score", "hrv", "rhr", "readiness", "temp_dev", "spo2", "steps",
         "activity_score", "sleep_duration", "stress_high", "deep_sleep",
         "rem_sleep", "resilience", "workouts")


def fmt(value, digits: int = 2) -> str:
    if value is None:
        return "n/a"
    if isinstance(value, (int, float)):
        return format(value, "." + str(digits) + "f")
    return str(value)


def period_means(series: dict, resolved: dict, start: str, end: str) -> dict:
    out = {}
    for name, metric in resolved.items():
        vals = [v for d, v in series[metric].items() if start <= d <= end]
        if vals:
            out[name] = {"mean": sum(vals) / len(vals), "n": len(vals),
                         "min": min(vals), "max": max(vals),
                         "sd": (sum((v - sum(vals) / len(vals)) ** 2 for v in vals) / len(vals)) ** 0.5}
    return out


def delta_line(name: str, cur: dict, prev: dict) -> str:
    if name not in cur:
        return "  - " + name + ": нет данных за текущее окно"
    now = cur[name]["mean"]
    if name not in prev:
        return "  - " + name + ": " + fmt(now) + " (нет сравнения)"
    before = prev[name]["mean"]
    diff = now - before
    arrow = "выше" if diff > 0 else ("ниже" if diff < 0 else "ровно")
    # Percent change is misleading for signed or near-zero baselines (e.g. temp_dev).
    show_pct = before > 0.5
    pct_part = (" / " + fmt(diff / before * 100.0, 1) + "%") if show_pct else " / —"
    return ("  - " + name + ": " + fmt(now) + " против " + fmt(before) +
            " (" + arrow + " на " + fmt(abs(diff)) + pct_part + ")")


def append_observations(pack: dict) -> list:
    """Append newly discovered regularities; idempotent by exact summary line."""
    pack = pack.get("signals", pack)  # v2.1 nests the signal block
    today = analytics.local_today().isoformat()
    text = OBS_PATH.read_text(encoding="utf-8") if OBS_PATH.exists() else "# Observations\n"
    added = []
    for p in pack["patterns"][:8]:
        summary = ("pattern: " + p["driver"] + " -> " + p["target"] + " | случаи: " +
                   str(p["occurrences"]) + "/" + str(p["of_opportunities"]) +
                   " | последний: " + p["last_seen"])
        if summary in text:
            continue
        entry = []
        entry.append("")
        entry.append("### " + today + " - " + summary)
        entry.append("Observation: " + p["driver"] + " в верхнем квартиле (>= " +
                     fmt(p["driver_threshold"]) + ") и " + p["target"] +
                     " ниже медианы на следующий день.")
        entry.append("Evidence: " + str(p["occurrences"]) + " из " +
                     str(p["of_opportunities"]) + " подходящих дней (" +
                     str(int(p["share"] * 100)) + "%), среднее изменение " +
                     fmt(p["mean_delta_next_day"]) + ", через день " +
                     fmt(p["mean_delta_day_after"]) + ", держится=" +
                     str(p["effect_holds_next_day"]) + ".")
        entry.append("Confidence: " + p["confidence"] + ".")
        entry.append("Possible explanation: отложенный эффект восстановления после нагрузки. Не доказано.")
        entry.append("Action: отслеживать повтор; при следующем случае назвать его по счёту.")
        text = text.rstrip() + "\n" + "\n".join(entry) + "\n"
        added.append(summary)
    if added:
        OBS_PATH.parent.mkdir(parents=True, exist_ok=True)
        OBS_PATH.write_text(text, encoding="utf-8")
    return added


def build(scope: str) -> dict:
    days = 7 if scope == "weekly" else 30
    full_pack = analytics.analyze(days_window=days + 7)
    generated_at = full_pack.get("generated_at")
    pack = full_pack.get("signals", full_pack)  # v2.1 nests the signal block
    con = analytics.connect()
    try:
        series = analytics.load_series(con)
        resolved = pack["canonical_metrics"]
        end = analytics.local_today()
        cur_start = (end - timedelta(days=days - 1)).isoformat()
        prev_end = (end - timedelta(days=days)).isoformat()
        prev_start = (end - timedelta(days=2 * days - 1)).isoformat()
        cur = period_means(series, resolved, cur_start, end.isoformat())
        prev = period_means(series, resolved, prev_start, prev_end)
    finally:
        con.close()
    added = append_observations(pack)
    title = "Weekly trend and pattern report" if scope == "weekly" else "Monthly deep personal analysis"
    lines = ["# " + title, "Date: " + end.isoformat(), 
             "Window: " + cur_start + " .. " + end.isoformat() + " vs " +
             prev_start + " .. " + prev_end, ""]
    lines.append("## Changed vs previous window")
    for name in FOCUS:
        if name in cur or name in prev:
            lines.append(delta_line(name, cur, prev))
    lines.append("")
    lines.append("## Trends (per 30 days, whole history)")
    for t in pack["trends"][:8]:
        lines.append("  - " + t["metric"] + ": " + fmt(t["slope_30d"], 3) +
                     " per 30d (n=" + str(t["n"]) + ", mean " + fmt(t["mean"]) + ")")
    lines.append("")
    lines.append("## Patterns")
    if pack["patterns"]:
        for p in pack["patterns"][:8]:
            lines.append("  - " + p["driver"] + " >= " + fmt(p["driver_threshold"]) +
                         " -> " + p["target"] + " ниже медианы: " +
                         str(p["occurrences"]) + "/" + str(p["of_opportunities"]) +
                         " (" + str(int(p["share"] * 100)) + "%), средний эффект " +
                         fmt(p["mean_delta_next_day"]) + ", через день " +
                         fmt(p["mean_delta_day_after"]) + ", confidence " +
                         p["confidence"] + ", последний " + p["last_seen"])
    else:
        lines.append("  - пока ни одной выше порога")
    lines.append("")
    lines.append("## Anomalies, last " + str(days) + " days")
    recent = [a for a in pack["anomalies"] if a["day"] >= cur_start]
    if recent:
        for a in recent[:10]:
            lines.append("  - " + a["day"] + " " + a["metric"] + " = " + fmt(a["value"]) +
                         " (rz " + fmt(a["robust_z"]) + ", median " + fmt(a["median"]) + ")")
    else:
        lines.append("  - нет")
    lines.append("")
    lines.append("## Lagged correlations (day d vs d+1)")
    for c in pack["correlations_lagged_1d"][:8]:
        lines.append("  - " + c["a"] + " -> " + c["b"] + ": r=" + fmt(c["r"], 3) +
                     " (n=" + str(c["n"]) + ")")
    lines.append("")
    lines.append("New regularities saved to observations.md: " + str(len(added)))
    text = "\n".join(lines)
    result = {"scope": scope, "generated_at": generated_at, "window": [cur_start, end.isoformat()],
              "previous_window": [prev_start, prev_end], "current": cur, "previous": prev,
              "trends": pack["trends"], "patterns": pack["patterns"],
              "anomalies": recent, "correlations_lagged_1d": pack["correlations_lagged_1d"],
              "observations_added": added, "briefing": text}
    analytics.save(result, "weekly.json" if scope == "weekly" else "monthly.json")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Oura trend and pattern report")
    parser.add_argument("--scope", choices=("weekly", "monthly"), default="weekly")
    args = parser.parse_args()
    result = build(args.scope)
    print(result["briefing"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
