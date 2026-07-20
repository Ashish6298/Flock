"""Unit tests for MetricsRegistry."""

import pytest
from flock.observability.exceptions import InvalidMetricError
from flock.observability.models import MetricType
from flock.observability.registry import MetricsRegistry


def test_registry_register_and_fetch() -> None:
    registry = MetricsRegistry()
    registry.register("test.counter", MetricType.COUNTER, {"service": "fsm"})

    registry.increment("test.counter", 5.0)
    registry.increment("test.counter", 2.0)

    val = registry.get_metric("test.counter")
    assert val is not None
    assert val.value == 7.0
    assert val.labels == {"service": "fsm"}


def test_registry_mismatched_types_raises() -> None:
    registry = MetricsRegistry()
    registry.register("metric-1", MetricType.COUNTER)
    
    with pytest.raises(InvalidMetricError):
        # Mismatched type registration
        registry.register("metric-1", MetricType.GAUGE)


def test_histogram_percentile_calculation() -> None:
    registry = MetricsRegistry()
    registry.register("test.latency", MetricType.HISTOGRAM)

    for latency in [10.0, 20.0, 30.0, 40.0, 50.0]:
        registry.observe("test.latency", latency)

    # 50th percentile (median) should be around 30.0
    p50 = registry.get_histogram_percentile("test.latency", 50.0)
    assert p50 == 30.0
