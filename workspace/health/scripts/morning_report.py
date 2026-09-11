#!/usr/bin/env python3
"""Short operational morning report.

Answers one question: how does the last night compare with this person's own
baseline. Prints a few lines, writes analysis/current.json. Facts only.
"""
from __future__ import annotations

import json
import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import analytics  # noqa: E402

BASE = Path(__file__).resolve().parents[1]
BASELINE_PATH = BASE / "analysis" / "baseline.json"

WATCH = (
    ("sleep_score", "Сон, балл"),
    ("hrv", "HRV, мс"),
    ("rhr", "Пульс покоя"),
    ("readiness", "Готовность"),
    ("temp_dev", "Температура, отклонение"),
    ("spo2", "SpO2, %"),
    ("breathing", "Дыхание, индекс"),
)


def fmt(value, digits: int = 1) -> str:
    if value is None:
        return "n/a"
    if isinstance(value, (int, float)):
        return format(value, "." + str(digits) + "f")
    return str(value)


def z_band(z: float) -> str:
    if z >= 1.5:
        return "выше обычного"
    if z <= -1.5:
        return "ниже обычного"
    return "в норме"


def main() -> int:
    pack = analytics.analyze(days_window=14)
    analytics.save(pack, "current.json")
    pack = pack.get("signals", pack)  # v2.1 nests the signal block
    metrics = pack["metrics"]

    yesterday = (date.today() - timedelta(days=1)).isoformat()
    lines = ["Отчёт за " + date.today().isoformat(), ""]
    flags = []
    for name, label in WATCH:
        m = metrics.get(name)
        if not m or m.get("n", 0) < analytics.MIN_DAYS_BASELINE:
            continue
        z = m.get("z_last", 0.0)
        lines.append("- " + label + ": " + fmt(m["last"]) + " (" + z_band(z) +
                     ", z " + fmt(z, 2) + "; медиана " + fmt(m["median"]) + ")")
        if abs(z) >= 2.0:
            flags.append(label + " " + fmt(m["last"]) + " — z " + fmt(z, 2))

    recent_anom = [a for a in pack["anomalies"] if a["day"] >= yesterday]
    lines.append("")
    if flags:
        lines.append("Отклонения: " + "; ".join(flags))
    else:
        lines.append("Отклонений нет: показатели в личном коридоре.")
    for a in recent_anom[:4]:
        lines.append("- аномалия " + a["day"] + ": " + a["metric"] + " = " +
                     fmt(a["value"]) + " (median " + fmt(a["median"]) + ")")
    if pack["patterns"]:
        top = pack["patterns"][0]
        lines.append("")
        lines.append("Наблюдаемая закономерность: " + top["driver"] + " -> " +
                     top["target"] + " на следующий день, случаев " +
                     str(top["occurrences"]) + "/" + str(top["of_opportunities"]) +
                     " (последний " + top["last_seen"] + ").")

    text = "\n".join(lines)
    out = BASE / "analysis"
    out.mkdir(parents=True, exist_ok=True)
    (out / "morning.md").write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
