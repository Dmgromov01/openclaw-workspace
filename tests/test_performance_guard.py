import json

from openclaw_modules.performance_guard import (
    Budget,
    TurnBudget,
    UsageEvent,
    append_usage,
    summarize_usage,
)


def test_turn_budget_caps_tools_retries_and_output():
    turn = TurnBudget(
        Budget(
            max_context_chars=4,
            max_tool_calls=2,
            max_tool_output_chars=5,
            max_retries=1,
        )
    )
    assert [turn.allow_tool_call(), turn.allow_tool_call(), turn.allow_tool_call()] == [True, True, False]
    assert [turn.allow_retry(), turn.allow_retry()] == [True, False]
    assert turn.trim_context("abcdef") == "abcd"
    assert turn.trim_tool_output({"value": "abcdef"}) == '{"val'


def test_usage_summary_contains_only_aggregates(tmp_path):
    events = [
        UsageEvent("2026-08-29T00:00:00Z", "main", "flash", "ok", 100, 10, 4, 3, 1, 0, 0, 0.01),
        UsageEvent("2026-08-29T00:01:00Z", "main", "flash", "error", 250, 20, 0, 0, 2, 1, 1, 0.0),
    ]
    target = tmp_path / "usage.jsonl"
    for event in events:
        append_usage(target, event)
    rows = [json.loads(line) for line in target.read_text().splitlines()]
    assert all("prompt" not in row and "response" not in row for row in rows)
    assert summarize_usage(events) == {
        "requests": 2,
        "input_tokens": 30,
        "output_tokens": 4,
        "cached_tokens": 3,
        "tool_calls": 3,
        "retries": 1,
        "compactions": 1,
        "latency_ms_total": 350,
        "estimated_cost_usd": 0.01,
    }


def test_usage_rejects_negative_counters():
    try:
        UsageEvent("now", "main", "flash", "ok", -1)
    except ValueError:
        pass
    else:
        raise AssertionError("negative latency must be rejected")
