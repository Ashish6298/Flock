"""Unit tests for MachineLearningPredictionEngine."""

import pytest
from flock.ai.exceptions import PredictionError
from flock.ai.models import PredictionRequest
from flock.ai.predictor import MachineLearningPredictionEngine


def test_prediction_engine_outputs() -> None:
    engine = MachineLearningPredictionEngine()
    req = PredictionRequest(predictor_name="test-predictor", features=[10.0, 5.0])

    res = engine.predict(req)
    assert res.prediction_value == (10.0 * 1.5 + 5.0 * 0.8)
    assert res.confidence == 0.95


def test_prediction_mismatched_features_raises() -> None:
    engine = MachineLearningPredictionEngine()
    req = PredictionRequest(predictor_name="test-predictor", features=[10.0])

    with pytest.raises(PredictionError):
        engine.predict(req)
