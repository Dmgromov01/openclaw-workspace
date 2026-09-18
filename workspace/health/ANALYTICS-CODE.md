# Аналитический слой Oura — код на ревью

**Статус: ни разу не запускалось.** python3 мне недоступен (allowlist), код писался без исполнения. Синтаксис вычитан, логика защитная, но первый прогон — твой.

Дата: 2026-09-11. Проект: /root/openclaw/workspace/health/

## Как это устроено

1. `oura_sync.py` выкачивает все 18 коллекций Oura в `data/oura.db`, таблица `oura_raw`.
2. `analytics.py` нормализует их в ЕДИНУЮ длинную таблицу `daily_facts(day, metric, value, n, agg)`.
   metric = коллекция + путь по JSON (`sleep.average_hrv`, `daily_readiness.score`), поэтому новые поля Oura не ломают схему.
3. Оттуда считаются: базовые линии (mean/sd/median/MAD/p10/p90), тренд (МНК-наклон за 30 дней),
   аномалии (robust z >= 3), корреляции (одновременные и A[d] -> B[d+1]), поведенческие паттерны.
4. Отчёты читают эти числа. **24 МБ в модель не отдаются — только десятки агрегатов.**

## Ключевые решения

- Нет хардкода полей: всё через рекурсивный обход JSON, поэтому схема терпима к изменениям.
- `heartrate` — высокочастотная коллекция (103k записей за 30 дней): хранится как среднее за день плюс min/max, а не как сырые 1000+ замеров.
- Канонические метрики (`hrv`, `rhr`, `readiness`, `spo2`, ...) разрешаются по списку кандидатов: если scope не выдан или поле переименовано — метрика просто выпадает, расчёт не падает.
- Паттерны считаются как повторяемость: драйвер в верхнем квартиле -> цель ниже медианы на следующий день.
  Именно это даёт фразу «это уже 7-й случай»: число случаев и средний эффект лежат в `memory/observations.md`.

## Риски, которые я вижу сам

- Пороги подобраны по опыту, не по данным: `MIN_OVERLAP_CORR = 20`, `CORR_MIN_ABS = 0.40`, аномалия `robust_z >= 3`, паттерн — доля случаев >= 15% и минимум 3 повтора.
- Корреляции на 30 днях статистически хрупкие: `n=20` даёт широкий доверительный интервал. Это подсказки, не выводы.
- `_pick_day` для `heartrate` берёт `timestamp[:10]` по UTC — на границе суток возможен сдвиг ±1 день относительно твоего московского дня.
- Агрегация по имени метрики (sum для steps/calories/duration, mean для остальных) — эвристика. Для дневных коллекций (одна запись в день) это неважно, для `sleep` с несколькими периодами за ночь возможно завышение.

## scripts/analytics.py

Ядро. Читает oura_raw (18 коллекций), нормализует в единую таблицу daily_facts(day, metric, value, n, agg), затем считает базовые статистики, тренды, аномалии, корреляции (одновременные и с лагом), паттерны. Пишет analysis/current.json.

```python
#!/usr/bin/env python3
"""Analytics core for the Oura data set.

Python computes. The model interprets (see AGENT.md).

Pipeline
--------
1. Read raw payloads from data/oura.db (table oura_raw, all 18 collections).
2. Normalize EVERY collection into ONE long-format daily fact table:
       daily_facts(day, metric, value, n, agg)
   metric = collection + "." + flattened json path, so the table survives Oura
   adding or renaming fields. Numeric leaves only; ids and timestamps skipped.
3. Reduce that table to compact statistics: baselines, trends, anomalies,
   concurrent and lagged correlations, and behavioural patterns.
4. Emit analysis/current.json. Report scripts import analyze().

Nothing here hands raw rows to the model: the output is a few dozen numbers.
"""
from __future__ import annotations

import json
import math
import sqlite3
import statistics
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
DB_PATH = BASE / "data" / "oura.db"
ANALYSIS_DIR = BASE / "analysis"

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
"""

SKIP_KEYS = {
    "id", "user_id", "time_zone", "offset", "day", "timestamp", "bedtime_start",
    "bedtime_end", "start_datetime", "end_datetime", "source", "period",
    "motion_count", "day_temperature", "label", "comment", "tags",
}

MEAN_HINTS = ("average", "avg", "mean", "score", "percentage", "percent", "rate",
              "deviation", "balance", "hrv", "bpm", "index", "efficiency",
              "latency", "temperature", "met")
SUM_HINTS = ("steps", "calories", "meters", "distance", "duration", "seconds",
             "time_in_bed", "awake_time", "non_wear_time", "resting_time",
             "sedentary_time", "activity_time", "inactivity", "samples", "count")

# Canonical metrics used for trends, correlations and reports. The first
# candidate present in the data wins, so missing scopes degrade, never crash.
CANONICAL = (
    ("hrv",            ("sleep.average_hrv", "sleep.hrv.average")),
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
    ("sleep_duration", ("daily_sleep.contributors.total_sleep",
                        "sleep.total_sleep_duration")),
    ("deep_sleep",     ("sleep.deep_sleep_duration",)),
    ("rem_sleep",      ("sleep.rem_sleep_duration",)),
    ("hr_avg",         ("heartrate.bpm",)),
    ("hr_max",         ("heartrate.bpm_max",)),
    ("hr_min",         ("heartrate.bpm_min",)),
    ("vascular_age",   ("daily_cardiovascular_age.vascular_age",)),
    ("workouts",       ("workout__items", "daily_activity__items")),
    ("sessions",       ("session__items",)),
    ("tags",           ("tag__items", "enhanced_tag__items")),
)

MIN_DAYS_BASELINE = 14
MIN_OVERLAP_CORR = 20
CORR_MIN_ABS = 0.40


# --------------------------------------------------------------------------- #
# storage helpers
# --------------------------------------------------------------------------- #

def connect() -> sqlite3.Connection:
    if not DB_PATH.exists():
        raise SystemExit("нет базы " + str(DB_PATH) + " - сначала oura_sync.py")
    con = sqlite3.connect(str(DB_PATH))
    con.executescript(FACT_SCHEMA)
    return con


def _is_number(v) -> bool:
    return (isinstance(v, (int, float)) and not isinstance(v, bool)
            and math.isfinite(float(v)))


def _pick_day(item_key: str, day_col, payload) -> str:
    """Best-effort day for one item, in priority order."""
    if day_col:
        return str(day_col)[:10]
    if isinstance(payload, dict):
        for key in ("day", "date"):
            v = payload.get(key)
            if isinstance(v, str) and len(v) >= 10:
                return v[:10]
        for key in ("timestamp", "bedtime_start", "start_datetime", "start_time"):
            v = payload.get(key)
            if isinstance(v, str) and len(v) >= 10:
                return v[:10]
    if isinstance(item_key, str) and len(item_key) >= 10 and item_key[4] == "-":
        return item_key[:10]
    return ""


def _flatten(obj, prefix: str, out: dict, depth: int = 0) -> None:
    """Collect numeric leaves as path -> [values]. Bounded depth."""
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


# --------------------------------------------------------------------------- #
# normalization: raw payloads -> daily_facts
# --------------------------------------------------------------------------- #

def normalize(con: sqlite3.Connection) -> dict:
    """Rebuild daily_facts from oura_raw. Returns a coverage report."""
    rows = con.execute(
        "SELECT endpoint, item_key, day, payload FROM oura_raw"
    ).fetchall()

    buckets: dict = {}          # day -> metric -> [values]
    endpoint_days: dict = {}    # endpoint -> set(days)
    endpoint_items: dict = {}   # endpoint -> item count
    hr_by_day: dict = {}        # day -> [bpm]

    for endpoint, item_key, day_col, payload_text in rows:
        try:
            payload = json.loads(payload_text) if payload_text else {}
        except (TypeError, ValueError):
            payload = {}
        day = _pick_day(item_key, day_col, payload)
        endpoint_items[endpoint] = endpoint_items.get(endpoint, 0) + 1
        if endpoint == "heartrate":
            bpm = payload.get("bpm") if isinstance(payload, dict) else None
            if _is_number(bpm) and day:
                hr_by_day.setdefault(day, []).append(float(bpm))
        if not day:
            continue
        endpoint_days.setdefault(endpoint, set()).add(day)
        leaves: dict = {}
        _flatten(payload, "", leaves, 0)
        per_day = buckets.setdefault(day, {})
        for path, values in leaves.items():
            per_day.setdefault(endpoint + "." + path, []).extend(values)

    # per-endpoint daily item counts (workouts/day, sessions/day, tags/day)
    for endpoint, days in endpoint_days.items():
        per_day_counts: dict = {}
        for d in days:
            per_day_counts[d] = 0
        for endpoint2, item_key, day_col, payload_text in rows:
            if endpoint2 != endpoint:
                continue
            try:
                payload = json.loads(payload_text) if payload_text else {}
            except (TypeError, ValueError):
                payload = {}
            d = _pick_day(item_key, day_col, payload)
            if d:
                per_day_counts[d] = per_day_counts.get(d, 0) + 1
        for d, c in per_day_counts.items():
            buckets.setdefault(d, {})[endpoint + "__items"] = [float(c)]

    # heart rate is high frequency: daily min and max matter, not just mean
    for d, values in hr_by_day.items():
        per_day = buckets.setdefault(d, {})
        per_day["heartrate.bpm_min"] = [min(values)]
        per_day["heartrate.bpm_max"] = [max(values)]

    fact_rows = []
    metric_set = set()
    for day, metrics in buckets.items():
        for metric, values in metrics.items():
            if not values:
                continue
            agg = _agg_for(metric)
            value = sum(values) if agg == "sum" else (sum(values) / len(values))
            fact_rows.append((day, metric, float(value), len(values), agg))
            metric_set.add(metric)

    con.executemany(
        "INSERT OR REPLACE INTO daily_facts (day, metric, value, n, agg) "
        "VALUES (?, ?, ?, ?, ?)",
        fact_rows,
    )
    con.commit()

    days = sorted(buckets)
    return {
        "raw_rows": len(rows),
        "fact_rows": len(fact_rows),
        "metrics": len(metric_set),
        "days": {"first": days[0] if days else None,
                 "last": days[-1] if days else None,
                 "count": len(days)},
        "endpoints": {e: {"items": endpoint_items.get(e, 0),
                          "days": len(endpoint_days.get(e, ()))}
                      for e in sorted(endpoint_items)},
    }


def load_series(con: sqlite3.Connection) -> dict:
    """metric -> {day: value} for every metric in the fact table."""
    series: dict = {}
    for day, metric, value in con.execute("SELECT day, metric, value FROM daily_facts"):
        series.setdefault(metric, {})[day] = float(value)
    return series


# --------------------------------------------------------------------------- #
# statistics
# --------------------------------------------------------------------------- #

def _quantile(sorted_values: list, q: float) -> float:
    if not sorted_values:
        return float("nan")
    if len(sorted_values) == 1:
        return sorted_values[0]
    pos = q * (len(sorted_values) - 1)
    low = int(math.floor(pos))
    high = min(low + 1, len(sorted_values) - 1)
    frac = pos - low
    return sorted_values[low] * (1 - frac) + sorted_values[high] * frac


def slope_per_30d(days: list, values: list) -> float:
    """Least-squares slope expressed per 30 days."""
    n = len(values)
    if n < 3:
        return 0.0
    x0 = date.fromisoformat(days[0])
    xs = [(date.fromisoformat(d) - x0).days for d in days]
    mean_x = sum(xs) / n
    mean_y = sum(values) / n
    sxx = sum((x - mean_x) ** 2 for x in xs)
    if sxx == 0:
        return 0.0
    sxy = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, values))
    return round((sxy / sxx) * 30.0, 5)


def describe(series_map: dict) -> dict:
    """Baseline statistics for one metric's {day: value} map."""
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
    last_value = values[-1]
    return {
        "n": n,
        "first_day": days[0],
        "last_day": days[-1],
        "mean": round(mean, 4),
        "sd": round(sd, 4),
        "median": round(median, 4),
        "mad": round(mad, 4),
        "p10": round(_quantile(ordered, 0.10), 4),
        "p90": round(_quantile(ordered, 0.90), 4),
        "min": round(ordered[0], 4),
        "max": round(ordered[-1], 4),
        "last": round(last_value, 4),
        "z_last": round((last_value - mean) / sd, 3) if sd > 0 else 0.0,
        "robust_z_last": round((last_value - median) / robust, 3) if robust > 0 else 0.0,
        "slope_30d": slope_per_30d(days, values),
    }


def pearson(a: dict, b: dict, lag: int = 0):
    """Pearson r between two {day: value} maps; b shifted by lag days."""
    pairs = []
    for day, x in a.items():
        target = (date.fromisoformat(day) + timedelta(days=lag)).isoformat()
        if target in b:
            pairs.append((x, b[target]))
    n = len(pairs)
    if n < MIN_OVERLAP_CORR:
        return None
    xs = [p[0] for p in pairs]
    ys = [p[1] for p in pairs]
    mean_x = sum(xs) / n
    mean_y = sum(ys) / n
    sxx = sum((x - mean_x) ** 2 for x in xs)
    syy = sum((y - mean_y) ** 2 for y in ys)
    if sxx <= 0 or syy <= 0:
        return None
    sxy = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys))
    return {"r": round(sxy / math.sqrt(sxx * syy), 3), "n": n}


def resolve_canonical(series: dict) -> dict:
    """Map canonical name -> real metric key, first available candidate."""
    resolved = {}
    for name, candidates in CANONICAL:
        for candidate in candidates:
            if candidate in series:
                resolved[name] = candidate
                break
    return resolved


def anomalies(series: dict, resolved: dict, limit: int = 25) -> list:
    """Days in the last 30 where a canonical metric is a robust outlier."""
    out = []
    cutoff = (date.today() - timedelta(days=30)).isoformat()
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
        for day in days:
            if day < cutoff:
                continue
            z = (data[day] - median) / robust
            if abs(z) >= 3.0:
                out.append({"day": day, "metric": name, "value": round(data[day], 3),
                            "median": round(median, 3), "robust_z": round(z, 2)})
    out.sort(key=lambda x: (x["day"], x["metric"]), reverse=True)
    return out[:limit]


def correlations(series: dict, resolved: dict, lag: int = 0, top: int = 12) -> list:
    """Top absolute-r pairs above threshold, with b shifted by lag days."""
    names = sorted(resolved)
    found = []
    for a in names:
        for b in names:
            if a == b:
                continue
            stat = pearson(series[resolved[a]], series[resolved[b]], lag=lag)
            if stat and abs(stat["r"]) >= CORR_MIN_ABS:
                found.append({"a": a, "b": b, "r": stat["r"], "n": stat["n"],
                              "lag_days": lag})
    found.sort(key=lambda x: abs(x["r"]), reverse=True)
    return found[:top]


def detect_patterns(series: dict, resolved: dict) -> list:
    """Repeating driver -> next-day effect patterns, counted.

    This is what lets the agent say "7th time after this kind of load" instead
    of only "HRV is low today".
    """
    patterns = []
    cutoff = (date.today() - timedelta(days=120)).isoformat()
    for driver in sorted(resolved):
        d_series = series[resolved[driver]]
        d_days = sorted(d for d in d_series if d >= cutoff)
        if len(d_days) < MIN_OVERLAP_CORR:
            continue
        d_values = sorted(d_series[d] for d in d_days)
        driver_high = _quantile(d_values, 0.75)
        for target in sorted(resolved):
            if target == driver:
                continue
            t_series = series[resolved[target]]
            if len(t_series) < MIN_OVERLAP_CORR:
                continue
            target_low = statistics.median(list(t_series.values()))
            cases = []
            for day in d_days:
                nxt = (date.fromisoformat(day) + timedelta(days=1)).isoformat()
                after = (date.fromisoformat(day) + timedelta(days=2)).isoformat()
                if d_series[day] < driver_high or nxt not in t_series:
                    continue
                if t_series[nxt] >= target_low:
                    continue
                delta1 = t_series[nxt] - t_series[day] if day in t_series else None
                delta2 = t_series[after] - t_series[nxt] if after in t_series else None
                cases.append((day, delta1, delta2))
            if len(cases) < 3:
                continue
            deltas1 = [c[1] for c in cases if c[1] is not None]
            deltas2 = [c[2] for c in cases if c[2] is not None]
            if not deltas1:
                continue
            mean1 = sum(deltas1) / len(deltas1)
            mean2 = sum(deltas2) / len(deltas2) if deltas2 else 0.0
            share = len(cases) / float(len(d_days))
            if share < 0.15:
                continue
            patterns.append({
                "driver": driver,
                "target": target,
                "occurrences": len(cases),
                "of_opportunities": len(d_days),
                "share": round(share, 2),
                "driver_threshold": round(driver_high, 3),
                "mean_delta_next_day": round(mean1, 3),
                "mean_delta_day_after": round(mean2, 3),
                "effect_holds_next_day": bool(abs(mean2) >= abs(mean1) * 0.6),
                "last_seen": cases[-1][0],
                "confidence": ("high" if len(cases) >= 8
                               else "medium" if len(cases) >= 5 else "low"),
            })
    patterns.sort(key=lambda p: (p["occurrences"], abs(p["mean_delta_next_day"])),
                  reverse=True)
    return patterns[:15]


def fact_preview(con: sqlite3.Connection, resolved: dict, days: int = 14) -> dict:
    """Compact recent slice of the canonical metrics for report scripts."""
    cutoff = (date.today() - timedelta(days=days)).isoformat()
    out = {}
    for name, metric in resolved.items():
        rows = con.execute(
            "SELECT day, value FROM daily_facts WHERE metric = ? AND day >= ? ORDER BY day",
            (metric, cutoff),
        ).fetchall()
        if rows:
            out[name] = {d: round(float(v), 3) for d, v in rows}
    return out


def analyze(days_window: int = 14) -> dict:
    """Full pass: normalize, then reduce to statistics."""
    con = connect()
    try:
        coverage = normalize(con)
        series = load_series(con)
        resolved = resolve_canonical(series)
        metrics = {}
        for name in resolved:
            metrics[name] = describe(series[resolved[name]])
        extra = sorted(((len(v), k) for k, v in series.items()
                        if len(v) >= MIN_DAYS_BASELINE), reverse=True)
        for _, metric in extra[:20]:
            if metric not in metrics:
                metrics[metric] = describe(series[metric])
        return {
            "generated_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
            "coverage": coverage,
            "canonical_metrics": resolved,
            "metrics": metrics,
            "trends": sorted(
                ({"metric": k, "slope_30d": v.get("slope_30d", 0.0),
                  "n": v.get("n", 0), "mean": v.get("mean"), "sd": v.get("sd")}
                 for k, v in metrics.items() if v.get("n", 0) >= MIN_DAYS_BASELINE),
                key=lambda x: abs(x["slope_30d"] or 0), reverse=True)[:15],
            "anomalies": anomalies(series, resolved),
            "correlations_concurrent": correlations(series, resolved, lag=0),
            "correlations_lagged_1d": correlations(series, resolved, lag=1),
            "patterns": detect_patterns(series, resolved),
            "recent": fact_preview(con, resolved, days_window),
        }
    finally:
        con.close()


def save(pack: dict, name: str = "current.json") -> Path:
    ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)
    path = ANALYSIS_DIR / name
    path.write_text(json.dumps(pack, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def main() -> int:
    pack = analyze()
    path = save(pack, "current.json")
    cov = pack["coverage"]
    print(json.dumps({
        "ok": True,
        "written": str(path),
        "raw_rows": cov["raw_rows"],
        "fact_rows": cov["fact_rows"],
        "metrics": cov["metrics"],
        "days": cov["days"],
        "canonical": len(pack["canonical_metrics"]),
        "anomalies": len(pack["anomalies"]),
        "patterns": len(pack["patterns"]),
        "correlations": {"concurrent": len(pack["correlations_concurrent"]),
                         "lagged": len(pack["correlations_lagged_1d"])},
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

## scripts/first_analysis.py

Deep Baseline Analysis — первый запуск. Строит baseline.json и первично заполняет memory/observations.md. Печатает компактный брифинг.

```python
#!/usr/bin/env python3
"""Deep Baseline Analysis - the FIRST run, not a morning report.

Builds the reference picture that daily and weekly reports compare against:
per-metric baselines, trends, anomalies, correlations and repeating patterns.
Writes analysis/baseline.json and seeds memory/observations.md, then prints a
compact briefing made of facts only. Raw rows are never printed.
"""
from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import analytics  # noqa: E402

BASE = Path(__file__).resolve().parents[1]
OBS_PATH = BASE / "memory" / "observations.md"
BASELINE_PATH = BASE / "analysis" / "baseline.json"

KEY_METRICS = ("sleep_score", "hrv", "rhr", "readiness", "temp_dev", "spo2",
               "steps", "activity_score", "sleep_duration", "stress_high",
               "deep_sleep", "rem_sleep", "resilience", "vascular_age")
OBS_HEADER = """# Observations

Наблюдения аналитического слоя Oura. Пишет Python (scripts/*), читает агент.
Формат: Observation / Evidence / Confidence / Possible explanation / Action.
Никаких диагнозов и никакой причинности из корреляции.
"""


def fmt(value, digits: int = 2) -> str:
    if value is None:
        return "n/a"
    if isinstance(value, (int, float)):
        return format(value, "." + str(digits) + "f")
    return str(value)


def briefing(pack: dict) -> str:
    cov = pack["coverage"]
    metrics = pack["metrics"]
    lines = []
    lines.append("# Deep Baseline Analysis")
    lines.append("Generated: " + str(pack["generated_at"]))
    lines.append("Raw rows: " + str(cov["raw_rows"]) + " | fact rows: " +
                 str(cov["fact_rows"]) + " | distinct metrics: " + str(cov["metrics"]))
    lines.append("Window: " + str(cov["days"]["first"]) + " .. " + str(cov["days"]["last"]) +
                 " (" + str(cov["days"]["count"]) + " days)")
    lines.append("")
    lines.append("## Collections ingested")
    for name in sorted(cov["endpoints"]):
        info = cov["endpoints"][name]
        lines.append("- " + name + ": " + str(info["items"]) + " items / " +
                     str(info["days"]) + " days")
    lines.append("")
    lines.append("## Baselines")
    for name in KEY_METRICS:
        m = metrics.get(name)
        if not m or m.get("n", 0) < analytics.MIN_DAYS_BASELINE:
            continue
        lines.append("- " + name + ": mean " + fmt(m["mean"]) + ", sd " + fmt(m["sd"]) +
                     ", median " + fmt(m["median"]) + ", p10-p90 " + fmt(m["p10"]) +
                     ".." + fmt(m["p90"]) + ", last " + fmt(m["last"]) +
                     " (z " + fmt(m["z_last"]) + "), slope/30d " + fmt(m["slope_30d"], 3) +
                     ", n=" + str(m["n"]))
    lines.append("")
    lines.append("## Strongest trends (per 30 days)")
    for t in pack["trends"][:8]:
        lines.append("- " + t["metric"] + ": " + fmt(t["slope_30d"], 3) +
                     " per 30d on mean " + fmt(t["mean"]) + " (n=" + str(t["n"]) + ")")
    lines.append("")
    lines.append("## Anomalies, last 30 days (robust z >= 3)")
    if pack["anomalies"]:
        for a in pack["anomalies"][:12]:
            lines.append("- " + a["day"] + " " + a["metric"] + " = " + fmt(a["value"]) +
                         " vs median " + fmt(a["median"]) + " (rz " + fmt(a["robust_z"]) + ")")
    else:
        lines.append("- none")
    lines.append("")
    lines.append("## Correlations, same day (|r| >= 0.4)")
    if pack["correlations_concurrent"]:
        for c in pack["correlations_concurrent"][:10]:
            lines.append("- " + c["a"] + " ~ " + c["b"] + ": r=" + fmt(c["r"], 3) +
                         " (n=" + str(c["n"]) + ")")
    else:
        lines.append("- none above threshold")
    lines.append("")
    lines.append("## Correlations, day d vs d+1 (|r| >= 0.4)")
    if pack["correlations_lagged_1d"]:
        for c in pack["correlations_lagged_1d"][:10]:
            lines.append("- " + c["a"] + " -> next-day " + c["b"] + ": r=" +
                         fmt(c["r"], 3) + " (n=" + str(c["n"]) + ")")
    else:
        lines.append("- none above threshold")
    lines.append("")
    lines.append("## Repeating patterns")
    if pack["patterns"]:
        for p in pack["patterns"][:10]:
            lines.append("- " + p["driver"] + " >= " + fmt(p["driver_threshold"]) +
                         " -> " + p["target"] + " below median next day: " +
                         str(p["occurrences"]) + "/" + str(p["of_opportunities"]) +
                         " times (" + str(int(p["share"] * 100)) + "%), mean delta " +
                         fmt(p["mean_delta_next_day"]) + ", day after " +
                         fmt(p["mean_delta_day_after"]) + ", holds=" +
                         str(p["effect_holds_next_day"]) + ", confidence " +
                         p["confidence"] + ", last seen " + p["last_seen"])
    else:
        lines.append("- none detected yet (need more days or stronger effects)")
    lines.append("")
    lines.append("## Data quality")
    sparse = [k for k, v in metrics.items() if v.get("n", 0) < analytics.MIN_DAYS_BASELINE]
    lines.append("- metrics below " + str(analytics.MIN_DAYS_BASELINE) +
                 " days (cannot be baselined yet): " + str(len(sparse)))
    lines.append("- limited to the synced window; absence of a metric may mean no data, not no signal")
    return "\n".join(lines)


def observations_block(pack: dict) -> str:
    today = date.today().isoformat()
    lines = ["", "## Baseline established " + today, ""]
    if not pack["patterns"]:
        lines.append("Patterns: nothing above threshold yet.")
    for p in pack["patterns"][:10]:
        lines.append("Observation: " + p["driver"] + " in the top quartile (>= " +
                     fmt(p["driver_threshold"]) + ") is followed by " + p["target"] +
                     " below its median the next day.")
        lines.append("Evidence: " + str(p["occurrences"]) + " of " +
                     str(p["of_opportunities"]) + " qualifying days (" +
                     str(int(p["share"] * 100)) + "%), mean change " +
                     fmt(p["mean_delta_next_day"]) + ", next day " +
                     fmt(p["mean_delta_day_after"]) + ". Last case " + p["last_seen"] + ".")
        lines.append("Confidence: " + p["confidence"] + ".")
        lines.append("Possible explanation: lagged recovery effect after a high-load day. Not established.")
        lines.append("Action: watch whether the same effect repeats, and log the 8th case explicitly.")
        lines.append("")
    return "\n".join(lines)


def main() -> int:
    pack = analytics.analyze(days_window=30)
    analytics.save(pack, "baseline.json")
    block = observations_block(pack)
    if not OBS_PATH.exists():
        OBS_PATH.parent.mkdir(parents=True, exist_ok=True)
        OBS_PATH.write_text(OBS_HEADER, encoding="utf-8")
    existing = OBS_PATH.read_text(encoding="utf-8")
    if "## Baseline established " + date.today().isoformat() not in existing:
        OBS_PATH.write_text(existing.rstrip() + "\n" + block, encoding="utf-8")
    text = briefing(pack)
    print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

## scripts/morning_report.py

Короткий операционный отчёт: последняя ночь против личного коридора. Пишет analysis/morning.md.

```python
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
```

## scripts/weekly_report.py

Недельный (--scope weekly) и месячный (--scope monthly) анализ трендов и паттернов. Пишет analysis/weekly.json или monthly.json и дописывает новые закономерности в observations.md.

```python
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
    pct = (diff / before * 100.0) if before else 0.0
    arrow = "выше" if diff > 0 else ("ниже" if diff < 0 else "ровно")
    return ("  - " + name + ": " + fmt(now) + " против " + fmt(before) +
            " (" + arrow + " на " + fmt(abs(diff)) + " / " + fmt(pct, 1) + "%)")


def append_observations(pack: dict) -> list:
    """Append newly discovered regularities; idempotent by exact summary line."""
    today = date.today().isoformat()
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
    pack = analytics.analyze(days_window=days + 7)
    con = analytics.connect()
    try:
        series = analytics.load_series(con)
        resolved = pack["canonical_metrics"]
        end = date.today()
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
    result = {"scope": scope, "generated_at": pack["generated_at"], "window": [cur_start, end.isoformat()],
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
```

## Запуск

```bash
cd /root/openclaw/workspace/health
python3 scripts/analytics.py        # проверка ядра, печатает покрытие
python3 scripts/first_analysis.py   # Deep Baseline Analysis
```

## Расписание автоматизаций (systemd user, Europe/Moscow)

```
health-morning  07:35 ежедневно   sync 7d  + morning report
health-weekly   Sun 10:00         sync 14d + weekly report
health-monthly  1-го 10:30        sync 45d + monthly report
```
