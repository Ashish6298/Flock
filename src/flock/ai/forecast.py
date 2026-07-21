"""Forecast Engine projecting telemetries growth."""

from __future__ import annotations

from typing import List

from flock.ai.exceptions import ForecastError
from flock.ai.models import ForecastResult


class ForecastEngine:
    """Computes linear projections matching delta trends."""

    def __init__(self) -> None:
        pass

    def forecast_trends(self, history: List[float], steps: int) -> ForecastResult:
        """Project values.

        Raises:
            ForecastError: If history elements size is less than 2.
        """
        if len(history) < 2:
            raise ForecastError("Forecasting trends requires at least 2 historical data samples.")

        # Heuristic: Simple linear extrapolation using last delta trend
        delta = history[-1] - history[-2]
        current = history[-1]
        
        projected = []
        for _ in range(steps):
            current += delta
            projected.append(current)

        return ForecastResult(forecasted_values=projected)
