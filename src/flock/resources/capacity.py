"""Capacity Planner forecasting cluster exhaustion parameters."""

from __future__ import annotations

import time
from typing import List

from flock.resources.models import CapacityForecast, NodeResourceProfile


class CapacityPlanner:
    """Estimates cluster exhaustion bounds by monitoring historical profiles."""

    def __init__(self) -> None:
        pass

    def generate_forecast(self, history: List[NodeResourceProfile]) -> CapacityForecast:
        """Analyze historic metrics to determine saturation trends.

        Args:
            history: List of recently logged node utilization data.
        """
        if not history:
            return CapacityForecast(
                exhaustion_timestamp=time.time() + 86400.0,  # 24 hours default
                forecast_growth_rate=0.0,
            )

        # Calculate average utilization
        avg_cpu = sum(h.cpu_util for h in history) / len(history)
        avg_mem = sum(h.memory_util for h in history) / len(history)

        alerts = []
        if avg_cpu > 80.0 or avg_mem > 80.0:
            alerts.append("High utilization pressure detected across nodes.")

        # Extrapolate linear trajectory
        growth_rate = 0.05  # assume 5% usage growth / hr mock rate
        time_to_exhaust = (100.0 - max(avg_cpu, avg_mem)) / (growth_rate or 0.01) * 3600.0

        return CapacityForecast(
            exhaustion_timestamp=time.time() + time_to_exhaust,
            forecast_growth_rate=growth_rate,
            alerts=alerts,
        )
