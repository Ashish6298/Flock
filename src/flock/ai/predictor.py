"""Machine Learning Prediction Engine."""

from __future__ import annotations

from typing import List

from flock.ai.exceptions import PredictionError
from flock.ai.models import PredictionRequest, PredictionResult


class MachineLearningPredictionEngine:
    """Predicts metrics values using lightweight linear heuristics."""

    def __init__(self) -> None:
        self.weights: List[float] = [1.5, 0.8]

    def predict(self, request: PredictionRequest) -> PredictionResult:
        """Calculate weighted projections.

        Raises:
            PredictionError: If request features size is invalid.
        """
        if len(request.features) != len(self.weights):
            raise PredictionError(
                f"Features size '{len(request.features)}' mismatches weights size '{len(self.weights)}'."
            )

        val = sum(f * w for f, w in zip(request.features, self.weights))
        return PredictionResult(prediction_value=val, confidence=0.95)
