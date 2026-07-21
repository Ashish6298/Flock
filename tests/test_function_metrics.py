"""Unit tests for FunctionMetrics."""

from flock.functions.models import FunctionMetrics


def test_metrics_initialization() -> None:
    metrics = FunctionMetrics(
        function_id="f1",
        invocation_count=50,
        error_count=2,
        avg_latency=12.5,
    )

    assert metrics.function_id == "f1"
    assert metrics.invocation_count == 50
    assert metrics.error_count == 2
    assert metrics.avg_latency == 12.5
