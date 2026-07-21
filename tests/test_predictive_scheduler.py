"""Unit tests for PredictiveScheduler."""

import pytest
from flock.ai.exceptions import OptimizationError
from flock.ai.scheduler import PredictiveScheduler


def test_predictive_scheduler_recommends_node() -> None:
    scheduler = PredictiveScheduler()
    loads = {"node-1": 0.8, "node-2": 0.3, "node-3": 0.5}

    # Recommends node with lowest CPU load
    assert scheduler.recommend_node(loads) == "node-2"


def test_predictive_scheduler_empty_loads_raises() -> None:
    scheduler = PredictiveScheduler()
    with pytest.raises(OptimizationError):
        scheduler.recommend_node({})
