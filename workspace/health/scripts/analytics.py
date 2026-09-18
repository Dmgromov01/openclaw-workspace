#!/usr/bin/env python3
"""Analytics core v2.1 for the Oura data set - production ready.

Python computes. The model interprets (see AGENT.md).

Layers, kept separate on purpose:
    raw facts      oura_raw + daily_facts + daily_context (SQLite, never sent)
    signals        baselines, trends, anomalies, correlations, patterns (JSON)
    observations   memory/observations.md (repeating patterns with case counts)

v2.1 over v2
------------
1  syntax: __future__ import, __name__ guard, no glued defs
2  save(): archive/<date>_<report>.json (was one file per day -> reports collided)
   plus a latest_<report>.json symlink, and a 90-day retention sweep
3  detect_patterns(): min_days=21, honest "insufficient_history" meta, and the
   window now uses min() - the earlier max() made the window a no-op
4  connect(): PRAGMA quick_check result is actually asserted
5  sleep biphasic: duration fields summed, level fields NOT summed
   (average_* duration-weighted, lowest_* min, rest from the main period)
6  lagged correlations require more overlap, with the expectation documented
7  config/canonical_metrics.yaml (optional) with a hardcoded fallback
8  daily_context table for tags and comments
9  data_quality(): coverage, gaps, longest gap
10 DEBUG via OURA_DEBUG, and main() never dies with a raw traceback
"""
from __future__ import annotations

import json
import math
import os
import sqlite3
import statistics
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

TZ_NAME = "Europe/Moscow"
try:
    from zoneinfo import ZoneInfo
    LOCAL_TZ = ZoneInfo(TZ_NAME)
except Exception:                                    # no tzdata -> fixed offset
    LOCAL_TZ = timezone(timedelta(hours=3), "MSK")

BASE = Path(__file__).resolve().parents[1]
DB_PATH = BASE / "data" / "oura.db"
ANALYSIS_DIR = BASE / "analysis"
CONFIG_DIR = BASE / "config"

DEBUG = os.environ.get("OURA_DEBUG", "").lower() in ("1", "true", "yes")
ARCHIVE_RETENTION_DAYS = 90

FACT_SCHEMA = """
CREATE TABLE IF NOT EXISTS daily_facts (
    day    TEXT NOT NULL,
    metric TEXT NOT NULL,
    value  REAL,
    n      INTEGER,
    agg    TEXT,
    PRIMARY KEY (day, metric)
);
CREATE INDEX IF NOT EXISTS idx_facts_metric ON daily_facts(metric);
CREATE TABLE IF NOT EXISTS daily_context (
    day     TEXT PRIMARY KEY,
    tags    TEXT,
    comment TEXT
);
"""

SKIP_KEYS = {
    "id", "user_id", "time_zone", "offset", "day", "timestamp", "bedtime_start",
    "bedtime_end", "start_datetime", "end_datetime", "start_time", "end_time",
    "source", "period", "motion_count", "day_temperature",
}

MEAN_HINTS = ("average", "avg", "mean", "score", "percentage", "percent", "rate",
              "deviation", "balance", "hrv", "bpm", "index", "efficiency",
              "latency", "temperature", "met", "level")
SUM_HINTS = ("steps", "calories", "meters", "distance", "duration", "seconds",
             "time_in_bed", "awake_time", "non_wear_time", "resting_time",
             "sedentary_time", "activity_time", "inactivity", "samples", "count")

# Sleep fields are NOT uniform: totals add up across periods, levels do not.
SLEEP_SUM_KEYS = ("total_sleep_duration", "deep_sleep_duration", "light_sleep_duration",
                  "rem_sleep_duration", "awake_time", "time_in_bed")
SLEEP_MIN_KEYS = ("lowest_heart_rate", "min_heart_rate")
SLEEP_AVG_KEYS = ("average_hrv", "average_heart_rate", "average_breath",
                  "average_heart_rate_variability")

# Oura returns some duration fields in seconds; store them as hours so that
# summary stats and anomaly detection use human-readable units.
SECONDS_TO_HOURS = {
    "daily_stress.recovery_high",
    "daily_stress.stress_high",
    "daily_stress.stress_seconds_high",
}

CANONICAL_FALLBACK = (
    ("hrv",            ("sleep.average_hrv",)),
    ("rhr",            ("sleep.lowest_heart_rate", "sleep.average_heart_rate")),
    ("sleep_score",    ("daily_sleep.score",)),
    ("readiness",      ("daily_readiness.score",)),
    ("activity_score", ("daily_activity.score",)),
    ("steps",          ("daily_activity.steps",)),
    ("calories",       ("daily_activity.total_calories", "daily_activity.active_calories")),
    ("temp_dev",       ("daily_readiness.temperature_deviation",)),
    ("spo2",           ("daily_spo2.spo2_percentage.average",)),
    ("breathing",      ("daily_spo2.breathing_disturbance_index",)),
    ("stress_high",    ("daily_stress.stress_high", "daily_stress.stress_seconds_high")),
    ("recovery_high",  ("daily_stress.recovery_high",)),
    ("resilience",     ("daily_resilience.contributors.sleep_recovery",
                        "daily_resilience.level")),
    ("sleep_duration", ("daily_sleep.contributors.total_sleep", "sleep.total_sleep_duration")),
    ("deep_sleep",     ("sleep.deep_sleep_duration",)),
    ("rem_sleep",      ("sleep.rem_sleep_duration",)),
    ("sleep_periods",  ("sleep__periods",)),
    ("nap_duration",   ("sleep__nap_duration",)),
    ("biphasic",       ("sleep__biphasic",)),
    # Raw/high-frequency heart-rate streams are intentionally excluded from
    # canonical health findings: they are vulnerable to motion/sampling
    # artefacts. Use sleep.lowest_heart_rate for the RHR signal instead.
    ("vascular_age",   ("daily_cardiovascular_age.vascular_age",)),
    ("workouts",       ("workout__items", "daily_activity__items")),
    ("workout_minutes", ("workout.total_duration",)),
    ("sessions",       ("session__items",)),
    ("tags",           ("tag__items", "enhanced_tag__items")),
)

MIN_DAYS_BASELINE = 14
MIN_OVERLAP_CORR = 30
ANOMALY_Z_THRESHOLD = 3.0
# hr_max is a daily maximum by construction; legitimate workout peaks can be
# far above the median. Use a higher threshold so only physiologically
# implausible values are flagged.
ANOMALY_THRESHOLDS = {"hr_max": 5.0}
# Lagged pairs need more overlap: two noisy series shifted by a day lose
# effective sample size. Expect EMPTY lagged correlations below ~40 days.
MIN_OVERLAP_LAGGED = 30
CORR_MIN_ABS = 0.40
# Repeating-pattern claims need a longer series than a one-month MVP.
PATTERN_MIN_DAYS = 60


# --------------------------------------------------------------------------- #
# config
# --------------------------------------------------------------------------- #

def load_canonical_config() -> tuple:
    """canonical metrics from YAML when present, hardcoded fallback otherwise."""
    config_path = CONFIG_DIR / "canonical_metrics.yaml"
    if config_path.exists():
        try:
            import yaml
            with open(config_path, encoding="utf-8") as handle:
                data = yaml.safe_load(handle) or {}
            metrics = data.get("metrics") or {}
            pairs = [(name, tuple(spec.get("candidates") or ()))
                     for name, spec in metrics.items() if spec.get("candidates")]
            if pairs:
                return tuple(pairs)
        except Exception as exc:                          # bad YAML must not kill us
            if DEBUG:
                print("[DEBUG] config load failed: " + str(exc), file=sys.stderr)
    return CANONICAL_FALLBACK


CANONICAL = load_canonical_config()


# --------------------------------------------------------------------------- #
# timezone
# --------------------------------------------------------------------------- #

def local_today() -> date:
    return datetime.now(LOCAL_TZ).date()


def to_local_day(value) -> str:
    """ISO 8601 timestamp -> local (Moscow) calendar day. Empty on failure."""
    if not isinstance(value, str) or len(value) < 10:
        return ""
    text = value.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return text[:10] if text[4] == "-" else ""
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(LOCAL_TZ).date().isoformat()


# --------------------------------------------------------------------------- #
# storage
# --------------------------------------------------------------------------- #

def connect() -> sqlite3.Connection:
    if not DB_PATH.exists():
        raise SystemExit("База не найдена: " + str(DB_PATH) + " - сначала oura_sync.py")
    try:
        con = sqlite3.connect(str(DB_PATH), timeout=30.0)
        check = con.execute("PRAGMA quick_check").fetchone()
        if not check or str(check[0]).lower() != "ok":
            raise SystemExit("База повреждена: " + str(check))
        con.executescript(FACT_SCHEMA)
        return con
    except sqlite3.DatabaseError as exc:
        raise SystemExit("Ошибка базы данных " + str(DB_PATH) + ": " + str(exc))


def _is_number(v) -> bool:
    return (isinstance(v, (int, float)) and not isinstance(v, bool)
            and math.isfinite(float(v)))


def _pick_day(item_key: str, day_col, payload) -> tuple:
    """Local day plus its source, so DEBUG can show why a day was chosen."""
    if isinstance(day_col, str) and len(day_col) >= 10 and day_col[4] == "-":
        return day_col[:10], "day_column"
    if isinstance(payload, dict):
        for key in ("day", "date"):
            v = payload.get(key)
            if isinstance(v, str) and len(v) >= 10 and v[4] == "-":
                return v[:10], "payload." + key
        for key in ("timestamp", "bedtime_start", "bedtime_end", "start_datetime",
                    "end_datetime", "start_time", "end_time"):
            converted = to_local_day(payload.get(key))
            if converted:
                return converted, "converted." + key
    if isinstance(item_key, str) and len(item_key) >= 10 and item_key[4] == "-":
        return item_key[:10], "item_key"
    return "", "unknown"


def _flatten(obj, prefix: str, out: dict, depth: int = 0) -> None:
    if depth > 4:
        return
    if isinstance(obj, dict):
        for key, value in obj.items():
            if key in SKIP_KEYS:
                continue
            path = prefix + "." + key if prefix else key
            if _is_number(value):
                out.setdefault(path, []).append(float(value))
            elif isinstance(value, (dict, list)):
                _flatten(value, path, out, depth + 1)
    elif isinstance(obj, list):
        for item in obj[:200]:
            if _is_number(item):
                out.setdefault(prefix, []).append(float(item))
            elif isinstance(item, (dict, list)):
                _flatten(item, prefix, out, depth + 1)


def _agg_for(metric: str) -> str:
    low = metric.lower()
    if any(h in low for h in MEAN_HINTS):
        return "mean"
    if any(h in low for h in SUM_HINTS):
        return "sum"
    return "mean"


def extract_context(payload: dict) -> tuple:
    """Tags and comment for daily_context. Sparse by nature: Oura tags are rare."""
    tags = []
    raw_tags = payload.get("tags")
    if isinstance(raw_tags, list):
        tags.extend(str(t) for t in raw_tags if t)
    for key in ("label", "custom_name", "tag_type_code"):
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            tags.append(value.strip())
    comment = ""
    if isinstance(payload.get("comment"), str):
        comment = payload["comment"].strip()
    return (", ".join(tags), comment)


# --------------------------------------------------------------------------- #
# sleep
# --------------------------------------------------------------------------- #

def process_sleep_periods(periods: list) -> dict:
    """Turn sleep periods for one day into metrics.

    Biphasic nights (two comparable periods) are NOT summed blindly: genuinely
    additive fields are summed, level fields are aggregated by semantics.
    """
    if not periods:
        return {}
    ordered = sorted(periods, key=lambda p: p[0], reverse=True)
    main_weight, main_payload = ordered[0]
    is_biphasic = len(ordered) >= 2 and ordered[1][0] > main_weight * 0.8
    primary = ordered[:2] if is_biphasic else ordered[:1]
    rest = ordered[2:] if is_biphasic else ordered[1:]

    nap_threshold = min(main_weight * 0.4, 10800.0)
    nap_total = sum(w for w, _ in rest if w < nap_threshold)

    result: dict = {}
    _flatten(main_payload, "", result, 0)
    result = {"sleep." + key: value for key, value in result.items()}

    def values_for(key: str):
        return [(float(payload[key]), weight) for weight, payload in primary
                if _is_number(payload.get(key))]

    keys = set()
    for _, payload in primary:
        keys.update(k for k, v in payload.items() if _is_number(v))

    for key in keys:
        pairs = values_for(key)
        if not pairs:
            continue
        if key in SLEEP_SUM_KEYS:
            result["sleep." + key] = [sum(v for v, _ in pairs)]
        elif key in SLEEP_MIN_KEYS:
            result["sleep." + key] = [min(v for v, _ in pairs)]
        elif key in SLEEP_AVG_KEYS:
            total_weight = sum(w for _, w in pairs) or 1.0
            result["sleep." + key] = [sum(v * w for v, w in pairs) / total_weight]
        else:
            result["sleep." + key] = [pairs[0][0]]        # main period wins

    result["sleep__periods"] = [float(len(periods))]
    result["sleep__nap_duration"] = [float(nap_total)]
    result["sleep__biphasic"] = [1.0 if is_biphasic else 0.0]
    return result


# --------------------------------------------------------------------------- #
# normalization
# --------------------------------------------------------------------------- #

def normalize(con: sqlite3.Connection) -> dict:
    rows = con.execute("SELECT endpoint, item_key, day, payload FROM oura_raw").fetchall()

    buckets: dict = {}
    endpoint_days: dict = {}
    endpoint_items: dict = {}
    hr_by_day: dict = {}
    sleep_by_day: dict = {}
    context_by_day: dict = {}

    for endpoint, item_key, day_col, payload_text in rows:
        try:
            payload = json.loads(payload_text) if payload_text else {}
        except (TypeError, ValueError):
            payload = {}
        if not isinstance(payload, dict):
            payload = {}
        day, _source = _pick_day(item_key, day_col, payload)
        endpoint_items[endpoint] = endpoint_items.get(endpoint, 0) + 1
        if DEBUG and day:
            print("[DEBUG] " + endpoint + " -> " + day, file=sys.stderr)

        if day:
            tags, comment = extract_context(payload)
            if tags or comment:
                old_tags, old_comment = context_by_day.get(day, ("", ""))
                merged_tags = ", ".join(t for t in (old_tags, tags) if t)
                merged_comment = " | ".join(c for c in (old_comment, comment) if c)
                context_by_day[day] = (merged_tags, merged_comment)

        if endpoint == "heartrate":
            bpm = payload.get("bpm")
            if _is_number(bpm) and day:
                hr_by_day.setdefault(day, []).append(float(bpm))
            continue
        if not day:
            continue
        endpoint_days.setdefault(endpoint, set()).add(day)
        if endpoint == "sleep":
            total = payload.get("total_sleep_duration")
            weight = float(total) if _is_number(total) else 0.0
            sleep_by_day.setdefault(day, []).append((weight, payload))
            continue
        leaves: dict = {}
        _flatten(payload, "", leaves, 0)
        per_day = buckets.setdefault(day, {})
        for path, values in leaves.items():
            per_day.setdefault(endpoint + "." + path, []).extend(values)

    for day, periods in sleep_by_day.items():
        buckets.setdefault(day, {}).update(process_sleep_periods(periods))

    counts: dict = {}
    for endpoint, item_key, day_col, payload_text in rows:
        if endpoint in ("heartrate", "sleep"):
            continue
        try:
            payload = json.loads(payload_text) if payload_text else {}
        except (TypeError, ValueError):
            payload = {}
        if not isinstance(payload, dict):
            payload = {}
        day, _source = _pick_day(item_key, day_col, payload)
        if day:
            counts.setdefault(endpoint, {})
            counts[endpoint][day] = counts[endpoint].get(day, 0) + 1
    for endpoint, per_day_counts in counts.items():
        for day, count in per_day_counts.items():
            buckets.setdefault(day, {})[endpoint + "__items"] = [float(count)]

    for day, values in hr_by_day.items():
        per_day = buckets.setdefault(day, {})
        per_day["heartrate.bpm_mean"] = [sum(values) / len(values)]
        per_day["heartrate.bpm_min"] = [min(values)]
        per_day["heartrate.bpm_max"] = [max(values)]
        per_day["heartrate.bpm_count"] = [float(len(values))]

    fact_rows = []
    metric_set = set()
    for day, metrics in buckets.items():
        for metric, values in metrics.items():
            if not values:
                continue
            if metric.startswith("sleep__") or metric.startswith("heartrate."):
                agg = "mean"
            else:
                agg = _agg_for(metric)
            value = sum(values) if agg == "sum" else (sum(values) / len(values))
            if metric in SECONDS_TO_HOURS:
                value = round(value / 3600.0, 2)
            fact_rows.append((day, metric, float(value), len(values), agg))
            metric_set.add(metric)

    con.executemany(
        "INSERT OR REPLACE INTO daily_facts (day, metric, value, n, agg) "
        "VALUES (?, ?, ?, ?, ?)", fact_rows)
    context_rows = [(day, tags, comment) for day, (tags, comment) in context_by_day.items()]
    con.executemany(
        "INSERT OR REPLACE INTO daily_context (day, tags, comment) VALUES (?, ?, ?)",
        context_rows)
    con.commit()

    days = sorted(set(list(buckets) + list(hr_by_day)))
    return {
        "raw_rows": len(rows),
        "fact_rows": len(fact_rows),
        "context_rows": len(context_rows),
        "metrics": len(metric_set),
        "timezone": TZ_NAME,
        "days": {"first": days[0] if days else None,
                 "last": days[-1] if days else None,
                 "count": len(days)},
        "endpoints": {e: {"items": endpoint_items.get(e, 0),
                          "days": len(endpoint_days.get(e, set()))}
                      for e in sorted(endpoint_items)},
    }


def load_series(con: sqlite3.Connection) -> dict:
    series: dict = {}
    for day, metric, value in con.execute("SELECT day, metric, value FROM daily_facts"):
        series.setdefault(metric, {})[day] = float(value)
    return series


# --------------------------------------------------------------------------- #
# data quality
# --------------------------------------------------------------------------- #

def data_quality(con: sqlite3.Connection, days: int = 30) -> dict:
    today = local_today()
    # Today is still in progress, so it is not expected to be covered yet.
    # The window is the last "days" complete days, and covered is bounded by
    # the same window, so coverage can never exceed 1.0.
    expected = {(today - timedelta(days=i)).isoformat() for i in range(1, days + 1)}
    cutoff = min(expected)
    covered = {row[0] for row in con.execute(
        "SELECT DISTINCT day FROM daily_facts WHERE day >= ?", (cutoff,)).fetchall()}
    covered &= expected
    gaps = sorted(expected - covered)

    gap_ranges = []
    if gaps:
        start = prev = gaps[0]
        for day in gaps[1:]:
            if (date.fromisoformat(day) - date.fromisoformat(prev)).days > 1:
                gap_ranges.append({"from": start, "to": prev})
                start = day
            prev = day
        gap_ranges.append({"from": start, "to": prev})

    longest = 0
    if gap_ranges:
        longest = max((date.fromisoformat(g["to"]) - date.fromisoformat(g["from"])).days + 1
                      for g in gap_ranges)
    return {"coverage": round(len(covered) / days, 3) if days else 0.0,
            "days_with_data": len(covered), "expected_days": days,
            "gaps": gap_ranges, "longest_gap_days": longest}


# --------------------------------------------------------------------------- #
# statistics
# --------------------------------------------------------------------------- #

def reliability(n: int) -> str:
    if n >= 60:
        return "stronger_evidence"
    if n >= 30:
        return "moderate"
    if n >= MIN_OVERLAP_CORR:
        return "exploratory"
    return "insufficient"


def _quantile(sorted_values: list, q: float) -> float:
    if not sorted_values:
        return float("nan")
    if len(sorted_values) == 1:
        return sorted_values[0]
    pos = q * (len(sorted_values) - 1)
    low = int(math.floor(pos))
    high = min(low + 1, len(sorted_values) - 1)
    return sorted_values[low] * (1 - (pos - low)) + sorted_values[high] * (pos - low)


def slope_per_30d(days: list, values: list) -> float:
    n = len(values)
    if n < 3:
        return 0.0
    x0 = date.fromisoformat(days[0])
    xs = [(date.fromisoformat(d) - x0).days for d in days]
    mean_x, mean_y = sum(xs) / n, sum(values) / n
    sxx = sum((x - mean_x) ** 2 for x in xs)
    if sxx == 0:
        return 0.0
    sxy = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, values))
    return round((sxy / sxx) * 30.0, 5)


def describe(series_map: dict) -> dict:
    days = sorted(series_map)
    values = [series_map[d] for d in days]
    n = len(values)
    if n == 0:
        return {"n": 0}
    ordered = sorted(values)
    mean = sum(values) / n
    sd = statistics.pstdev(values) if n > 1 else 0.0
    median = statistics.median(values)
    mad = statistics.median([abs(v - median) for v in values]) if n > 1 else 0.0
    robust = 1.4826 * mad if mad > 0 else sd
    return {"n": n, "first_day": days[0], "last_day": days[-1],
            "mean": round(mean, 4), "sd": round(sd, 4), "median": round(median, 4),
            "mad": round(mad, 4), "p10": round(_quantile(ordered, 0.10), 4),
            "p90": round(_quantile(ordered, 0.90), 4), "min": round(ordered[0], 4),
            "max": round(ordered[-1], 4), "last": round(values[-1], 4),
            "z_last": round((values[-1] - mean) / sd, 3) if sd > 0 else 0.0,
            "robust_z_last": round((values[-1] - median) / robust, 3) if robust > 0 else 0.0,
            "slope_30d": slope_per_30d(days, values),
            "reliability": reliability(n)}


def pearson(a: dict, b: dict, lag: int = 0):
    pairs = []
    for day, x in a.items():
        target = (date.fromisoformat(day) + timedelta(days=lag)).isoformat()
        if target in b:
            pairs.append((x, b[target]))
    n = len(pairs)
    min_required = MIN_OVERLAP_LAGGED if lag > 0 else MIN_OVERLAP_CORR
    if n < min_required:
        return None
    xs = [p[0] for p in pairs]
    ys = [p[1] for p in pairs]
    mean_x, mean_y = sum(xs) / n, sum(ys) / n
    sxx = sum((x - mean_x) ** 2 for x in xs)
    syy = sum((y - mean_y) ** 2 for y in ys)
    if sxx <= 0 or syy <= 0:
        return None
    sxy = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys))
    return {"r": round(sxy / math.sqrt(sxx * syy), 3), "n": n}


def resolve_canonical(series: dict) -> dict:
    resolved = {}
    for name, candidates in CANONICAL:
        for candidate in candidates:
            if candidate in series:
                resolved[name] = candidate
                break
    return resolved


def anomalies(series: dict, resolved: dict, limit: int = 25) -> list:
    out = []
    cutoff = (local_today() - timedelta(days=30)).isoformat()
    for name, metric in resolved.items():
        data = series[metric]
        days = sorted(data)
        values = [data[d] for d in days]
        if len(values) < MIN_DAYS_BASELINE:
            continue
        median = statistics.median(values)
        mad = statistics.median([abs(v - median) for v in values])
        robust = 1.4826 * mad
        if robust <= 0:
            continue
        threshold = ANOMALY_THRESHOLDS.get(name, ANOMALY_Z_THRESHOLD)
        flagged = [day for day in days
                   if day >= cutoff and abs((data[day] - median) / robust) >= threshold]
        if not flagged:
            continue
        # v1-compatible share: flagged days over the baseline days scanned
        share = round(len(flagged) / float(len(days)), 3)
        for day in flagged:
            z = (data[day] - median) / robust
            out.append({"day": day, "metric": name, "value": round(data[day], 3),
                        "median": round(median, 3), "robust_z": round(z, 2),
                        "share": share})
    out.sort(key=lambda x: (x["day"], x["metric"]), reverse=True)
    return out[:limit]


def correlations(series: dict, resolved: dict, lag: int = 0, top: int = 12) -> list:
    names = sorted(resolved)
    found = []
    for a in names:
        for b in names:
            if a == b:
                continue
            stat = pearson(series[resolved[a]], series[resolved[b]], lag=lag)
            if stat and abs(stat["r"]) >= CORR_MIN_ABS:
                found.append({"a": a, "b": b, "r": stat["r"], "n": stat["n"],
                              "lag_days": lag, "reliability": reliability(stat["n"]),
                              "confidence": reliability(stat["n"]),
                              "reading": "association only, not causation"})
    found.sort(key=lambda x: abs(x["r"]), reverse=True)
    return found[:top]


def detect_patterns(series: dict, resolved: dict,
                    min_days: int = PATTERN_MIN_DAYS, max_days: int = 180) -> tuple:
    """Repeating driver -> next-day effect with the confound controlled.

    Returns (patterns, meta). meta says honestly whether there was enough
    history, instead of silently returning an empty list.
    """
    all_days = sorted({d for s in series.values() for d in s})
    meta = {"days_available": len(all_days), "min_days_required": min_days}
    if len(all_days) < min_days:
        meta["insufficient_history"] = True
        return [], meta
    meta["insufficient_history"] = False
    window = min(max_days, max(min_days, int(len(all_days) * 0.6)))
    meta["window_days"] = window
    cutoff = (local_today() - timedelta(days=window)).isoformat()

    patterns = []
    for driver in sorted(resolved):
        d_series = series[resolved[driver]]
        d_days = sorted(d for d in d_series if d >= cutoff)
        if len(d_days) < MIN_OVERLAP_CORR:
            continue
        driver_high = _quantile(sorted(d_series[d] for d in d_days), 0.75)
        for target in sorted(resolved):
            if target == driver:
                continue
            t_series = series[resolved[target]]
            if len(t_series) < MIN_OVERLAP_CORR:
                continue
            target_median = statistics.median(list(t_series.values()))
            t_sd = statistics.pstdev(list(t_series.values())) if len(t_series) > 1 else 0.0
            cases, control = [], []
            for day in d_days:
                nxt = (date.fromisoformat(day) + timedelta(days=1)).isoformat()
                if nxt not in t_series:
                    continue
                today = t_series.get(day)
                prev = (date.fromisoformat(day) - timedelta(days=1)).isoformat()
                prev_value = t_series.get(prev)
                item = {"day": day, "target_today": today,
                        "target_next_day": t_series[nxt], "target_prev_day": prev_value,
                        "delta_next": (t_series[nxt] - today) if today is not None else None,
                        "delta_prev": ((today - prev_value)
                                       if (today is not None and prev_value is not None) else None)}
                if d_series[day] >= driver_high:
                    cases.append(item)
                else:
                    control.append(item)
            if len(cases) < 3 or len(control) < 5:
                continue
            eligible = [c for c in cases if c["target_today"] is not None
                        and c["target_today"] >= target_median]
            # Symmetric selection: controls must clear the same bar as cases,
            # otherwise cases are picked for a high "today" and their delta_next
            # is biased low by regression to the mean.
            control = [c for c in control if c["target_today"] is not None
                       and c["target_today"] >= target_median]
            if len(eligible) < 3 or len(control) < 5:
                continue
            confounded = len(cases) - len(eligible)
            if len(eligible) < 3:
                continue
            deltas = [c["delta_next"] for c in eligible if c["delta_next"] is not None]
            control_deltas = [c["delta_next"] for c in control if c["delta_next"] is not None]
            if not deltas or not control_deltas:
                continue
            mean_delta = sum(deltas) / len(deltas)
            mean_control = sum(control_deltas) / len(control_deltas)
            effect = mean_delta - mean_control
            if t_sd > 0 and abs(effect) < 0.35 * t_sd:
                continue
            consistency = sum(1 for d in deltas
                              if (d < 0) == (mean_delta < 0)) / float(len(deltas))
            after_deltas = []
            for c in eligible:
                after = (date.fromisoformat(c["day"]) + timedelta(days=2)).isoformat()
                prev = (date.fromisoformat(after) - timedelta(days=1)).isoformat()
                if after in t_series and prev in t_series:
                    after_deltas.append(t_series[after] - t_series[prev])
            n = len(eligible)
            band = reliability(n)
            confidence = ("high" if band == "stronger_evidence" and consistency >= 0.7
                          else "medium" if (band in ("moderate", "stronger_evidence")
                                            or consistency >= 0.7) else "low")
            patterns.append({
                "driver": driver, "target": target,
                "driver_threshold": round(driver_high, 3),
                "cases_considered": len(cases), "cases_eligible": n,
                "confounded_excluded": confounded, "of_opportunities": len(d_days),
                "share": round(n / float(len(d_days)), 2),
                "target_median": round(target_median, 3),
                "target_today_mean": round(sum(c["target_today"] for c in eligible) / n, 3),
                "target_next_day_mean": round(sum(c["target_next_day"] for c in eligible) / n, 3),
                "mean_delta_next_day": round(mean_delta, 3),
                "mean_delta_control": round(mean_control, 3),
                "effect_size": round(effect, 3),
                "mean_delta_day_after": round(sum(after_deltas) / len(after_deltas), 3)
                if after_deltas else 0.0,
                "direction": "down" if mean_delta < 0 else "up",
                "consistency": round(consistency, 2), "n": n,
                # v1-compatible alias so existing report consumers keep working
                "occurrences": n,
                "effect_holds_next_day": bool(
                    after_deltas and (mean_delta < 0) == ((sum(after_deltas) / len(after_deltas)) < 0)),
                "reliability": band, "confidence": confidence,
                "last_seen": eligible[-1]["day"],
                "examples": [c["day"] for c in eligible[-5:]],
                "reading": "group effect, never a rule for a single day"})
    patterns.sort(key=lambda p: (p["cases_eligible"], abs(p["effect_size"])), reverse=True)
    return patterns[:15], meta


def fact_preview(con: sqlite3.Connection, resolved: dict, days: int = 14) -> dict:
    cutoff = (local_today() - timedelta(days=days)).isoformat()
    out = {}
    for name, metric in resolved.items():
        rows = con.execute(
            "SELECT day, value FROM daily_facts WHERE metric = ? AND day >= ? ORDER BY day",
            (metric, cutoff)).fetchall()
        if rows:
            out[name] = {d: round(float(v), 3) for d, v in rows}
    return out


def analyze(days_window: int = 14) -> dict:
    con = connect()
    try:
        coverage = normalize(con)
        series = load_series(con)
        resolved = resolve_canonical(series)
        metrics = {name: describe(series[resolved[name]]) for name in resolved}
        extra = sorted(((len(v), k) for k, v in series.items()
                        if len(v) >= MIN_DAYS_BASELINE), reverse=True)
        for _, metric in extra[:20]:
            if metric not in metrics:
                metrics[metric] = describe(series[metric])
        patterns, patterns_meta = detect_patterns(series, resolved)
        signals = {
            "canonical_metrics": resolved,
            "metrics": metrics,
            "trends": sorted(
                ({"metric": k, "slope_30d": v.get("slope_30d", 0.0), "n": v.get("n", 0),
                  "mean": v.get("mean"), "sd": v.get("sd"),
                  "reliability": reliability(v.get("n", 0))}
                 for k, v in metrics.items() if v.get("n", 0) >= MIN_DAYS_BASELINE),
                key=lambda x: abs(x["slope_30d"] or 0), reverse=True)[:15],
            "anomalies": anomalies(series, resolved),
            "correlations_concurrent": correlations(series, resolved, lag=0),
            "correlations_lagged_1d": correlations(series, resolved, lag=1),
            "patterns": patterns,
            "patterns_meta": patterns_meta,
            "interpretation_policy": {
                "minimum_days_for_patterns": PATTERN_MIN_DAYS,
                "minimum_overlap_for_correlation": MIN_OVERLAP_CORR,
                "minimum_overlap_for_lagged_correlation": MIN_OVERLAP_LAGGED,
                "raw_heartrate_canonical": False,
                "note": "correlations are exploratory associations, never causation",
            },
        }
        return {
            "generated_at": datetime.now(LOCAL_TZ).isoformat(timespec="seconds"),
            "timezone": TZ_NAME,
            "version": "2.1",
            "layers": {"raw": "oura_raw + daily_facts + daily_context (SQLite)",
                       "signals": "this JSON",
                       "observations": "memory/observations.md"},
            "raw": coverage,
            "signals": signals,
            "quality": data_quality(con, days=30),
            "context": {"rows": coverage.get("context_rows", 0),
                        "note": "sparse by design: needs tags in the Oura app"},
            "recent": fact_preview(con, resolved, days_window),
        }
    finally:
        con.close()


def save(pack: dict, name: str = "current.json") -> Path:
    """Archive per (day, report) so reports never overwrite each other."""
    ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)
    archive = ANALYSIS_DIR / "archive"
    archive.mkdir(exist_ok=True)
    payload = json.dumps(pack, ensure_ascii=False, indent=2)
    stem = Path(name).stem
    now = datetime.now(LOCAL_TZ)
    versioned = archive / (local_today().isoformat() + "_" + now.strftime("%H%M%S") + "_" + stem + ".json")
    versioned.write_text(payload, encoding="utf-8")
    current = ANALYSIS_DIR / name
    current.write_text(payload, encoding="utf-8")
    latest = ANALYSIS_DIR / ("latest_" + stem + ".json")
    try:
        if latest.exists() or latest.is_symlink():
            latest.unlink()
        os.symlink(versioned, latest)
    except OSError:
        latest.write_text(payload, encoding="utf-8")
    cutoff = local_today() - timedelta(days=ARCHIVE_RETENTION_DAYS)
    for old in archive.glob("*.json"):
        try:
            file_date = date.fromisoformat(old.name[:10])
        except ValueError:
            continue
        if file_date < cutoff:
            old.unlink()
    return current


def main() -> int:
    try:
        pack = analyze()
        path = save(pack, "current.json")
        raw, sig, qual = pack["raw"], pack["signals"], pack["quality"]
        print(json.dumps({
            "ok": True, "version": pack["version"], "written": str(path),
            "timezone": pack["timezone"], "raw_rows": raw["raw_rows"],
            "fact_rows": raw["fact_rows"], "context_rows": raw.get("context_rows", 0),
            "metrics": raw["metrics"], "days": raw["days"],
            "canonical": len(sig["canonical_metrics"]),
            "anomalies": len(sig["anomalies"]), "patterns": len(sig["patterns"]),
            "patterns_meta": sig["patterns_meta"],
            "correlations": {"concurrent": len(sig["correlations_concurrent"]),
                             "lagged": len(sig["correlations_lagged_1d"])},
            "quality": qual,
        }, ensure_ascii=False, indent=2))
        return 0
    except KeyboardInterrupt:
        print(json.dumps({"ok": False, "error": "прервано пользователем"}))
        return 130
    except Exception as exc:
        import traceback
        print(json.dumps({"ok": False, "error": str(exc),
                          "traceback": traceback.format_exc()},
                         ensure_ascii=False, indent=2))
        return 1


if __name__ == "__main__":
    sys.exit(main())