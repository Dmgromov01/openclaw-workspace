"""Dependency-free execution guard for effective OpenClaw agents.

This module models task intent and completion checks at an adapter boundary. It
never calls a model, executes tools, or stores task text. Integrations can use it
to make the agent verify outcomes instead of merely producing plausible prose.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Iterable


class TaskKind(str, Enum):
    FAST = "fast"
    RESEARCH = "research"
    CODING = "coding"
    DEEP = "deep"
    VISION = "vision"


@dataclass(frozen=True)
class TaskProfile:
    """Execution policy for a class of tasks."""

    kind: TaskKind
    max_steps: int
    requires_external_sources: bool = False
    requires_verification: bool = True
    max_retries: int = 1


PROFILES: dict[TaskKind, TaskProfile] = {
    TaskKind.FAST: TaskProfile(TaskKind.FAST, max_steps=2, requires_verification=False),
    TaskKind.RESEARCH: TaskProfile(TaskKind.RESEARCH, max_steps=6, requires_external_sources=True),
    TaskKind.CODING: TaskProfile(TaskKind.CODING, max_steps=8),
    TaskKind.DEEP: TaskProfile(TaskKind.DEEP, max_steps=10),
    TaskKind.VISION: TaskProfile(TaskKind.VISION, max_steps=4),
}


@dataclass
class ExecutionPlan:
    """Small state machine for a single user task."""

    goal: str
    profile: TaskProfile
    acceptance_criteria: tuple[str, ...]
    completed: list[str] = field(default_factory=list)
    failed: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.goal.strip():
            raise ValueError("goal must not be empty")
        if not self.acceptance_criteria:
            raise ValueError("at least one acceptance criterion is required")

    @property
    def steps_used(self) -> int:
        return len(self.completed) + len(self.failed)

    def record(self, step: str, *, ok: bool) -> None:
        if not step.strip():
            raise ValueError("step must not be empty")
        if self.steps_used >= self.profile.max_steps:
            raise RuntimeError("execution step budget exhausted")
        (self.completed if ok else self.failed).append(step)

    def verify(self, satisfied: Iterable[str]) -> bool:
        """Return true only when every declared criterion is satisfied."""
        observed = {item.strip() for item in satisfied if item.strip()}
        return all(criterion in observed for criterion in self.acceptance_criteria)

    def next_action(self, *, verified: bool, last_step_failed: bool) -> str:
        if verified:
            return "finish"
        if last_step_failed and len(self.failed) <= self.profile.max_retries:
            return "retry"
        if self.steps_used >= self.profile.max_steps:
            return "ask"
        return "continue"


def make_plan(goal: str, kind: TaskKind, acceptance_criteria: Iterable[str]) -> ExecutionPlan:
    """Create a normalized plan without retaining the original task elsewhere."""
    criteria = tuple(dict.fromkeys(item.strip() for item in acceptance_criteria if item.strip()))
    return ExecutionPlan(goal=goal.strip(), profile=PROFILES[kind], acceptance_criteria=criteria)
