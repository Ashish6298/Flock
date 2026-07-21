"""Learning Engine updating model parameters."""

from __future__ import annotations

from typing import List

from flock.ai.exceptions import LearningError
from flock.ai.models import LearningSnapshot


class LearningEngine:
    """Simulates training model loops dynamically."""

    def __init__(self) -> None:
        self.loss = 0.5
        self.iterations = 0

    def learn_step(self, feedback: List[float]) -> LearningSnapshot:
        """Update model coefficients.

        Raises:
            LearningError: If feedback metrics array is empty.
        """
        if not feedback:
            raise LearningError("Feedback parameter list cannot be empty.")

        self.iterations += 1
        # Model updates: Loss slowly decreases with training steps
        self.loss = max(self.loss - 0.05 * sum(feedback) / len(feedback), 0.01)
        return LearningSnapshot(loss=self.loss, iterations=self.iterations)
