"""Unit tests for AIMetrics."""

from flock.ai.models import OptimizationMetrics


def test_optimization_metrics_savings() -> None:
    metrics = OptimizationMetrics(savings_percentage=15.5)
    assert metrics.savings_percentage == 15.5
