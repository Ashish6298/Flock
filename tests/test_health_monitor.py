"""Unit tests for HealthMonitor."""

import asyncio
from typing import Dict, Any
import pytest
from flock.events.bus import EventBus
from flock.observability.health import HealthMonitor
from flock.observability.models import MetricType
from flock.observability.registry import MetricsRegistry


@pytest.mark.asyncio
async def test_health_monitor_evaluates_status() -> None:
    registry = MetricsRegistry()
    events = EventBus()
    monitor = HealthMonitor("node-1", registry, events)

    report = monitor.evaluate_health()
    assert report.status == "HEALTHY"

    # Simulate health degradation using registry metrics
    registry.register("flock.storage.wal_corruptions.total", MetricType.COUNTER)
    registry.increment("flock.storage.wal_corruptions.total", 1.0)

    report_degraded = monitor.evaluate_health()
    assert report_degraded.status == "UNHEALTHY"
