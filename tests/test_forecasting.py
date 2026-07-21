"""Unit tests for ForecastEngine."""

import pytest
from flock.ai.exceptions import ForecastError
from flock.ai.forecast import ForecastEngine


def test_forecast_trends_calculation() -> None:
    engine = ForecastEngine()
    history = [10.0, 12.0, 14.0]

    # Predicts delta projections
    res = engine.forecast_trends(history, steps=2)
    assert res.forecasted_values == [16.0, 18.0]


def test_forecast_insufficient_history_raises() -> None:
    engine = ForecastEngine()
    with pytest.raises(ForecastError):
        engine.forecast_trends([10.0], steps=2)
