# analytics.py v2 — на ревью

**Статус: НЕ применён и ни разу не запускался.** Файл на диске пока остаётся v1. Это черновик на твоё «ок».

## Что исправлено — построчно по твоим замечаниям

**1. Timezone.** Появились `local_today()` и `to_local_day()`, зона `Europe/Moscow` через `zoneinfo` (при отсутствии tzdata — фиксированный +03:00). Все окна считаются от московской даты. Oura-поле `day` остаётся главным; таймстемпы теперь **конвертируются**, а не обрезаются `[:10]`. Это правит сдвиг ночных и вечерних записей heartrate на соседний день.

**2. Sleep.** Для коллекции `sleep` больше не работает эвристика по имени поля. Выбирается **основной период дня** (максимальный `total_sleep_duration`), и метрики берутся только из него. Дневной сон вынесен отдельно: `sleep__periods` (число периодов) и `sleep__nap_duration` (суммарно вне основного).

**3. Надёжность по n.** Функция `reliability()`: `exploratory` 20–29, `moderate` 30–59, `stronger_evidence` ≥60 (меньше 20 — `insufficient`). Полоса проставлена в корреляциях, трендах, базовых статистиках и паттернах. Рядом с каждой корреляцией — `reading: association only, not causation`, чтобы агент не формулировал «X вызывает Y».

**4. Паттерны с контролем конфаунда.** Главная правка. Случай засчитывается, только если цель **не была уже ниже медианы** в день драйвера (`cases_eligible`), исключённые считаются отдельно (`confounded_excluded`). Плюс контрольная когорта дней с низким драйвером, и эффект считается как разность с ней (`effect_size`), а не сам по себе. Если эффект меньше 0.35 sd цели — паттерн отбрасывается как шум. В каждом паттерне теперь `target_today_mean`, `target_next_day_mean`, `mean_delta_control`, `consistency`, `n`, `reliability`, `examples`.

**5. date.today() убран.** Ни одного вызова `date.today()` не осталось — только `local_today()`. Серверная зона (сейчас UTC) на аналитическое окно не влияет.

## Побочно

- `heartrate` пропускает общий проход по JSON: обрабатывается явно (mean/min/max/count). Это и корректнее, и заметно быстрее.
- Три слоя разведены в самом JSON: `layers` + `raw` (покрытие из SQLite) + `signals` (метрики, тренды, аномалии, корреляции, паттерны) + указатель на `observations`.

## Что изменится на диске после твоего ок

- `scripts/analytics.py` — заменяется на v2;
- `first_analysis.py`, `morning_report.py`, `weekly_report.py` — перевожу на слой `signals` и московские даты;
- `deploy/health-*.timer` — **удаляю**, systemd-планирование отменяется;
- расписание переносится в **OpenClaw cron** (`openclaw cron add --cron ... --command ...`), Gateway — единственный планировщик, Python — исполнитель.

## Код

```python
#!/usr/bin/env python3
"""Analytics core v2 for the Oura data set.

Python computes. The model interprets (see AGENT.md).

Three layers, kept separate on purpose:
    raw facts      oura_raw + daily_facts (SQLite only, never sent to the model)
    signals        baselines, trends, anomalies, correlations, patterns (JSON)
    observations   memory/observations.md (repeating patterns with case counts)

v2 fixes over v1
----------------
* Every day is computed in Europe/Moscow, never in the server timezone. Oura's
  own day field stays authoritative; timestamps are converted, not truncated.
  Missing tzdata falls back to a fixed +03:00 offset.
* Sleep is not summed blindly: the main period per day is selected (longest
  total_sleep_duration) and naps are reported as a separate metric.
* heartrate is high frequency and is handled explicitly (mean/min/max/count);
  it skips the generic flattening pass, which also keeps the run fast.
* Correlations and patterns carry n plus a reliability band:
  exploratory 20-29, moderate 30-59, stronger_evidence >= 60.
* detect_patterns controls the confound: a case counts only when the target was
  NOT already below its median on the driver day, and the effect is compared
  with a control cohort of non-high driver days. Per-case fields are reported,
  not just group means.
"""
from __future__ import annotations

import json
import math
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
    "bedtime_end", "start_datetime", "end_datetime", "start_time", "end_time",
    "source", "period", "motion_count", "day_temperature", "label", "comment",
    "tags",
}

MEAN_HINTS = ("average", "avg", "mean", "score", "percentage", "percent", "rate",
              "deviation", "balance", "hrv", "bpm", "index", "efficiency",
              "latency", "temperature", "met", "level")
SUM_HINTS = ("steps", "calories", "meters", "distance", "duration", "seconds",
             "time_in_bed", "awake_time", "non_wear_time", "resting_time",
             "sedentary_time", "activity_time", "inactivity", "samples", "count")

CANONICAL = (
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
    ("hr_avg",         ("heartrate.bpm_mean", "heartrate.bpm")),
    ("hr_max",         ("heartrate.bpm_max",)),
    ("hr_min",         ("heartrate.bpm_min",)),
    ("vascular_age",   ("daily_cardiovascular_age.vascular_age",)),
    ("workouts",       ("workout__items", "daily_activity__items")),
    ("workout_minutes", ("workout.total_duration",)),
    ("sessions",       ("session__items",)),
    ("tags",           ("tag__items", "enhanced_tag__items")),
)

MIN_DAYS_BASELINE = 14
MIN_OVERLAP_CORR = 20
CORR_MIN_ABS = 0.40


# --------------------------------------------------------------------------- #
# timezone helpers
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
        raise SystemExit("нет базы " + str(DB_PATH) + " - сначала oura_sync.py")
    con = sqlite3.connect(str(DB_PATH))
    con.executescript(FACT_SCHEMA)
    return con


def _is_number(v) -> bool:
    return (isinstance(v, (int, float)) and not isinstance(v, bool)
            and math.isfinite(float(v)))


def _pick_day(item_key: str, day_col, payload) -> str:
    """Local day for one item. Oura's own day field wins, always."""
    if isinstance(day_col, str) and len(day_col) >= 10 and day_col[4] == "-":
        return day_col[:10]
    if isinstance(payload, dict):
        for key in ("day", "date"):
            v = payload.get(key)
            if isinstance(v, str) and len(v) >= 10 and v[4] == "-":
                return v[:10]
        for key in ("timestamp", "bedtime_start", "bedtime_end", "start_datetime",
                    "end_datetime", "start_time", "end_time"):
            converted = to_local_day(payload.get(key))
            if converted:
                return converted
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
    """Aggregation for collections that legitimately hold several items a day."""
    low = metric.lower()
    if any(h in low for h in MEAN_HINTS):
        return "mean"
    if any(h in low for h in SUM_HINTS):
        return "sum"
    return "mean"


# --------------------------------------------------------------------------- #
# normalization
# --------------------------------------------------------------------------- #

def normalize(con: sqlite3.Connection) -> dict:
    """Rebuild daily_facts from oura_raw. Returns a coverage report."""
    rows = con.execute("SELECT endpoint, item_key, day, payload FROM oura_raw").fetchall()

    buckets: dict = {}
    endpoint_days: dict = {}
    endpoint_items: dict = {}
    hr_by_day: dict = {}
    sleep_by_day: dict = {}

    for endpoint, item_key, day_col, payload_text in rows:
        try:
            payload = json.loads(payload_text) if payload_text else {}
        except (TypeError, ValueError):
            payload = {}
        if not isinstance(payload, dict):
            payload = {}
        day = _pick_day(item_key, day_col, payload)
        endpoint_items[endpoint] = endpoint_items.get(endpoint, 0) + 1

        if endpoint == "heartrate":
            bpm = payload.get("bpm")
            if _is_number(bpm) and day:
                hr_by_day.setdefault(day, []).append(float(bpm))
            continue                                   # skip generic flattening

        if not day:
            continue
        endpoint_days.setdefault(endpoint, set()).add(day)

        if endpoint == "sleep":
            total = payload.get("total_sleep_duration")
            weight = float(total) if _is_number(total) else 0.0
            sleep_by_day.setdefault(day, []).append((weight, payload))
            continue                                   # dedicated sleep rule

        leaves: dict = {}
        _flatten(payload, "", leaves, 0)
        per_day = buckets.setdefault(day, {})
        for path, values in leaves.items():
            per_day.setdefault(endpoint + "." + path, []).extend(values)

    # --- sleep: one main period per day, naps measured separately -----------
    for day, periods in sleep_by_day.items():
        total_main = periods[0][0]
        main = periods[0][1]
        for weight, payload in periods:
            if weight > total_main:
                total_main, main = weight, payload
        leaves: dict = {}
        _flatten(main, "", leaves, 0)
        per_day = buckets.setdefault(day, {})
        for path, values in leaves.items():
            per_day["sleep." + path] = values            # main period only
        nap_sum = sum(p[0] for p in periods)
        per_day["sleep__periods"] = [float(len(periods))]
        per_day["sleep__nap_duration"] = [float(max(0.0, nap_sum - total_main))]

    # --- per-endpoint daily item counts (workouts, sessions, tags) ----------
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
        day = _pick_day(item_key, day_col, payload)
        if day:
            counts.setdefault(endpoint, {})
            counts[endpoint][day] = counts[endpoint].get(day, 0) + 1
    for endpoint, per_day_counts in counts.items():
        for day, count in per_day_counts.items():
            buckets.setdefault(day, {})[endpoint + "__items"] = [float(count)]

    # --- heartrate: daily mean/min/max plus sample count --------------------
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
            fact_rows.append((day, metric, float(value), len(values), agg))
            metric_set.add(metric)

    con.executemany(
        "INSERT OR REPLACE INTO daily_facts (day, metric, value, n, agg) "
        "VALUES (?, ?, ?, ?, ?)",
        fact_rows,
    )
    con.commit()

    days = sorted(set(list(buckets) + list(hr_by_day)))
    return {
        "raw_rows": len(rows),
        "fact_rows": len(fact_rows),
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
# statistics
# --------------------------------------------------------------------------- #

def reliability(n: int) -> str:
    """How much weight an association deserves. Guards against over-reading r."""
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
    mean_x = sum(xs) / n
    mean_y = sum(values) / n
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
        "last": round(values[-1], 4),
        "z_last": round((values[-1] - mean) / sd, 3) if sd > 0 else 0.0,
        "robust_z_last": round((values[-1] - median) / robust, 3) if robust > 0 else 0.0,
        "slope_30d": slope_per_30d(days, values),
        "reliability": reliability(n),
    }


def pearson(a: dict, b: dict, lag: int = 0):
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
    names = sorted(resolved)
    found = []
    for a in names:
        for b in names:
            if a == b:
                continue
            stat = pearson(series[resolved[a]], series[resolved[b]], lag=lag)
            if stat and abs(stat["r"]) >= CORR_MIN_ABS:
                found.append({
                    "a": a, "b": b, "r": stat["r"], "n": stat["n"],
                    "lag_days": lag,
                    "reliability": reliability(stat["n"]),
                    "reading": "association only, not causation",
                })
    found.sort(key=lambda x: abs(x["r"]), reverse=True)
    return found[:top]


def detect_patterns(series: dict, resolved: dict) -> list:
    """Repeating driver -> next-day effect, with the confound controlled.

    A high-driver day counts as a case only when the target was NOT already
    below its median on that same day, and the effect is compared with a
    control cohort of non-high driver days. Without that control the pattern
    would merely restate that the target was already low.
    """
    patterns = []
    cutoff = (local_today() - timedelta(days=120)).isoformat()
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
            t_values = list(t_series.values())
            target_median = statistics.median(t_values)
            t_sd = statistics.pstdev(t_values) if len(t_values) > 1 else 0.0

            cases = []
            control = []
            for day in d_days:
                nxt = (date.fromisoformat(day) + timedelta(days=1)).isoformat()
                if nxt not in t_series:
                    continue
                today = t_series.get(day)
                prev = (date.fromisoformat(day) - timedelta(days=1)).isoformat()
                prev_value = t_series.get(prev)
                item = {
                    "day": day,
                    "target_today": today,
                    "target_next_day": t_series[nxt],
                    "target_prev_day": prev_value,
                    "delta_next": (t_series[nxt] - today) if today is not None else None,
                    "delta_prev": ((today - prev_value)
                                   if (today is not None and prev_value is not None) else None),
                }
                if d_series[day] >= driver_high:
                    cases.append(item)
                else:
                    control.append(item)

            if len(cases) < 3 or len(control) < 5:
                continue
            eligible = [c for c in cases
                        if c["target_today"] is not None
                        and c["target_today"] >= target_median]
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
                continue                                   # effect within noise
            consistency = sum(1 for d in deltas
                              if (d < 0) == (mean_delta < 0)) / float(len(deltas))
            after_deltas = []
            for c in eligible:
                after = (date.fromisoformat(c["day"]) + timedelta(days=2)).isoformat()
                prev = (date.fromisoformat(after) - timedelta(days=1)).isoformat()
                if after in t_series and prev in t_series:
                    after_deltas.append(t_series[after] - t_series[prev])
            mean_day_after = (sum(after_deltas) / len(after_deltas)) if after_deltas else 0.0
            n = len(eligible)
            band = reliability(n)
            confidence = ("high" if band == "stronger_evidence" and consistency >= 0.7
                          else "medium" if (band in ("moderate", "stronger_evidence")
                                            or consistency >= 0.7)
                          else "low")
            patterns.append({
                "driver": driver,
                "target": target,
                "driver_threshold": round(driver_high, 3),
                "cases_considered": len(cases),
                "cases_eligible": n,
                "confounded_excluded": confounded,
                "of_opportunities": len(d_days),
                "share": round(n / float(len(d_days)), 2),
                "target_median": round(target_median, 3),
                "target_today_mean": round(sum(c["target_today"] for c in eligible) / n, 3),
                "target_next_day_mean": round(sum(c["target_next_day"] for c in eligible) / n, 3),
                "mean_delta_next_day": round(mean_delta, 3),
                "mean_delta_control": round(mean_control, 3),
                "effect_size": round(effect, 3),
                "mean_delta_day_after": round(mean_day_after, 3),
                "direction": "down" if mean_delta < 0 else "up",
                "consistency": round(consistency, 2),
                "n": n,
                "reliability": band,
                "confidence": confidence,
                "last_seen": eligible[-1]["day"],
                "examples": [c["day"] for c in eligible[-5:]],
                "reading": "group effect, never a rule for a single day",
            })
    patterns.sort(key=lambda p: (p["cases_eligible"], abs(p["effect_size"])), reverse=True)
    return patterns[:15]


def fact_preview(con: sqlite3.Connection, resolved: dict, days: int = 14) -> dict:
    cutoff = (local_today() - timedelta(days=days)).isoformat()
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
    """Full pass. Returns raw coverage, signals, and the observations pointer."""
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
        signals = {
            "canonical_metrics": resolved,
            "metrics": metrics,
            "trends": sorted(
                ({"metric": k, "slope_30d": v.get("slope_30d", 0.0),
                  "n": v.get("n", 0), "mean": v.get("mean"), "sd": v.get("sd"),
                  "reliability": reliability(v.get("n", 0))}
                 for k, v in metrics.items() if v.get("n", 0) >= MIN_DAYS_BASELINE),
                key=lambda x: abs(x["slope_30d"] or 0), reverse=True)[:15],
            "anomalies": anomalies(series, resolved),
            "correlations_concurrent": correlations(series, resolved, lag=0),
            "correlations_lagged_1d": correlations(series, resolved, lag=1),
            "patterns": detect_patterns(series, resolved),
        }
        return {
            "generated_at": datetime.now(LOCAL_TZ).isoformat(timespec="seconds"),
            "timezone": TZ_NAME,
            "layers": {"raw": "oura_raw + daily_facts (SQLite, never sent to the model)",
                       "signals": "this JSON",
                       "observations": "memory/observations.md"},
            "raw": coverage,
            "signals": signals,
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
    raw = pack["raw"]
    sig = pack["signals"]
    print(json.dumps({
        "ok": True,
        "written": str(path),
        "timezone": pack["timezone"],
        "raw_rows": raw["raw_rows"],
        "fact_rows": raw["fact_rows"],
        "metrics": raw["metrics"],
        "days": raw["days"],
        "canonical": len(sig["canonical_metrics"]),
        "anomalies": len(sig["anomalies"]),
        "patterns": len(sig["patterns"]),
        "correlations": {"concurrent": len(sig["correlations_concurrent"]),
                         "lagged": len(sig["correlations_lagged_1d"])},
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
```
