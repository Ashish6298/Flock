"""Unit tests for AutoScalingEngine."""

import pytest
from flock.functions.exceptions import ScalePolicyError
from flock.functions.scaling import AutoScalingEngine


def test_autoscaling_heuristic() -> None:
    engine = AutoScalingEngine(min_replicas=1, max_replicas=5)

    # Concurrency 0 returns min_replicas target
    assert engine.calculate_replicas(3, 0) == 1

    # Low concurrency keeps current replicas
    assert engine.calculate_replicas(3, 2) == 3

    # High concurrency triggers scale increment
    assert engine.calculate_replicas(3, 10) == 4


def test_autoscaling_negative_replicas_raises() -> None:
    engine = AutoScalingEngine()

    with pytest.raises(ScalePolicyError):
        engine.calculate_replicas(-1, 5)
