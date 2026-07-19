"""Unit tests validating RecoveryRegistry tracking and worker cooldown exclusions."""

import pytest
import time
from flock.recovery.models import RetryContext, RecoveryPlan
from flock.recovery.registry import RecoveryRegistry
from flock.recovery.exceptions import DuplicateRecoveryError

def test_recovery_registry_operations() -> None:
    registry = RecoveryRegistry()
    ctx = RetryContext(task_id="task-1", attempt_count=1)

    registry.update_context(ctx)
    assert registry.get_context("task-1") == ctx

    # Cooldown verification
    assert registry.is_cooling_down("worker-1") is False
    registry.register_cooldown("worker-1", duration_sec=1.0)
    assert registry.is_cooling_down("worker-1") is True
    time.sleep(1.1)
    assert registry.is_cooling_down("worker-1") is False

    # Plans registration
    plan = RecoveryPlan(task_id="task-1", target_node_id="worker-2")
    registry.register_plan(plan)
    assert registry.get_plan("task-1") == plan

    # Duplicate plan register check
    with pytest.raises(DuplicateRecoveryError):
        registry.register_plan(plan)
