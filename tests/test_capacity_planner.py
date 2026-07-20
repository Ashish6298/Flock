"""Unit tests for CapacityPlanner."""

import time
from flock.resources.capacity import CapacityPlanner
from flock.resources.models import NodeResourceProfile


def test_capacity_forecasting() -> None:
    planner = CapacityPlanner()
    
    # 90% loaded node list
    history = [
        NodeResourceProfile(node_id="n1", cpu_cores=8, cpu_util=90.0, memory_mb=100, memory_util=10)
    ]

    forecast = planner.generate_forecast(history)
    assert len(forecast.alerts) == 1
    assert "High utilization pressure" in forecast.alerts[0]
    assert forecast.exhaustion_timestamp > time.time()
