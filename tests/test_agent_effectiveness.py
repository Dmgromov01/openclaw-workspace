import pytest

from openclaw_modules.agent_effectiveness import (
    PROFILES,
    TaskKind,
    make_plan,
)


def test_plan_deduplicates_criteria_and_requires_verification():
    plan = make_plan("deploy fix", TaskKind.CODING, ["tests pass", "tests pass", "service healthy"])
    assert plan.acceptance_criteria == ("tests pass", "service healthy")
    assert plan.profile is PROFILES[TaskKind.CODING]
    assert plan.next_action(verified=False, last_step_failed=False) == "continue"
    plan.record("implement", ok=True)
    plan.record("test", ok=True)
    assert plan.verify(["tests pass", "service healthy"])
    assert plan.next_action(verified=True, last_step_failed=False) == "finish"


def test_plan_retries_once_then_continues_with_steps_left():
    plan = make_plan("investigate", TaskKind.RESEARCH, ["source checked"])
    plan.record("fetch", ok=False)
    assert plan.next_action(verified=False, last_step_failed=True) == "retry"
    plan.record("fetch retry", ok=False)
    assert plan.next_action(verified=False, last_step_failed=True) == "continue"


def test_profiles_have_bounded_steps():
    assert all(profile.max_steps > 0 for profile in PROFILES.values())
    with pytest.raises(ValueError):
        make_plan("", TaskKind.FAST, ["done"])
    with pytest.raises(ValueError):
        make_plan("task", TaskKind.FAST, [])
