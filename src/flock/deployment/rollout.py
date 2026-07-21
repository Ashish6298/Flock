"""Rollout Engine implementing strategy state transitions."""

from __future__ import annotations

from flock.deployment.exceptions import RolloutFailedError
from flock.deployment.models import RolloutState


class RolloutEngine:
    """Updates rollout progress percentages and states."""

    def __init__(self) -> None:
        pass

    def advance_rollout(self, state: RolloutState, progress_delta: float) -> RolloutState:
        """Increment progress metrics. Transition status on completion.

        Raises:
            RolloutFailedError: If progress delta is invalid.
        """
        if progress_delta < 0:
            raise RolloutFailedError("Progress increment delta cannot be negative.")

        new_progress = min(state.progress_percentage + progress_delta, 100.0)
        status = "IN_PROGRESS"
        if new_progress >= 100.0:
            status = "COMPLETED"

        return RolloutState(
            deployment_id=state.deployment_id,
            strategy=state.strategy,
            batch_size=state.batch_size,
            progress_percentage=new_progress,
            status=status,
        )
