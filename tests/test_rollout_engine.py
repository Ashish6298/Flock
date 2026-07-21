"""Unit tests for RolloutEngine."""

import pytest
from flock.deployment.exceptions import RolloutFailedError
from flock.deployment.models import RolloutState
from flock.deployment.rollout import RolloutEngine


def test_rollout_incremental_progress() -> None:
    engine = RolloutEngine()
    state = RolloutState(deployment_id="dep-1", strategy="CANARY")

    # Advancing progress updates state properties
    state_in_progress = engine.advance_rollout(state, 50.0)
    assert state_in_progress.progress_percentage == 50.0
    assert state_in_progress.status == "IN_PROGRESS"

    # Delta exceeding 100 sets status to COMPLETED
    state_completed = engine.advance_rollout(state_in_progress, 60.0)
    assert state_completed.progress_percentage == 100.0
    assert state_completed.status == "COMPLETED"


def test_rollout_negative_delta_raises() -> None:
    engine = RolloutEngine()
    state = RolloutState(deployment_id="dep-1", strategy="CANARY")

    with pytest.raises(RolloutFailedError):
        engine.advance_rollout(state, -10.0)
