"""Small, dependency-free budgets and usage ledger for OpenClaw adapters.

The module deliberately does not call OpenClaw or any provider. Integrations can
use it at their boundary to cap tool output/retries and record aggregate usage
without persisting prompts, responses, tokens, or credentials.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path
from typing import Any, Iterable


@dataclass(frozen=True)
class Budget:
    """Per-turn safety limits for an adapter or tool runner."""

    max_context_chars: int = 320_000
    max_tool_calls: int = 5
    max_tool_output_chars: int = 12_000
    max_retries: int = 1

    def __post_init__(self) -> None:
        for name in ("max_context_chars", "max_tool_calls", "max_tool_output_chars"):
            if getattr(self, name) < 1:
                raise ValueError(f"{name} must be positive")
        if self.max_retries < 0:
            raise ValueError("max_retries must not be negative")


class TurnBudget:
    """Track and enforce tool-call/retry budgets for one turn."""

    def __init__(self, budget: Budget | None = None) -> None:
        self.budget = budget or Budget()
        self.tool_calls = 0
        self.retries = 0

    def allow_tool_call(self) -> bool:
        if self.tool_calls >= self.budget.max_tool_calls:
            return False
        self.tool_calls += 1
        return True

    def allow_retry(self) -> bool:
        if self.retries >= self.budget.max_retries:
            return False
        self.retries += 1
        return True

    def trim_context(self, value: str) -> str:
        return value[: self.budget.max_context_chars]

    def trim_tool_output(self, value: Any) -> str:
        text = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False, default=str)
        return text[: self.budget.max_tool_output_chars]


@dataclass(frozen=True)
class UsageEvent:
    """Aggregate-only event; never put prompt/response text in this record."""

    timestamp: str
    agent: str
    model: str
    status: str
    latency_ms: int
    input_tokens: int = 0
    output_tokens: int = 0
    cached_tokens: int = 0
    tool_calls: int = 0
    retries: int = 0
    compactions: int = 0
    estimated_cost_usd: float = 0.0

    def __post_init__(self) -> None:
        if self.latency_ms < 0 or any(
            value < 0
            for value in (
                self.input_tokens,
                self.output_tokens,
                self.cached_tokens,
                self.tool_calls,
                self.retries,
                self.compactions,
                self.estimated_cost_usd,
            )
        ):
            raise ValueError("usage counters must not be negative")

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False, sort_keys=True)


def append_usage(path: str | Path, event: UsageEvent) -> None:
    """Append one aggregate event, creating a private parent directory/file."""
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("a", encoding="utf-8") as stream:
        stream.write(event.to_json() + "\n")


def summarize_usage(events: Iterable[UsageEvent]) -> dict[str, int | float]:
    """Return totals suitable for a dashboard or daily alert."""
    rows = list(events)
    return {
        "requests": len(rows),
        "input_tokens": sum(row.input_tokens for row in rows),
        "output_tokens": sum(row.output_tokens for row in rows),
        "cached_tokens": sum(row.cached_tokens for row in rows),
        "tool_calls": sum(row.tool_calls for row in rows),
        "retries": sum(row.retries for row in rows),
        "compactions": sum(row.compactions for row in rows),
        "latency_ms_total": sum(row.latency_ms for row in rows),
        "estimated_cost_usd": round(sum(row.estimated_cost_usd for row in rows), 6),
    }
