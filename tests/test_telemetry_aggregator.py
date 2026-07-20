"""Unit tests for TelemetryAggregator."""

import asyncio
from unittest.mock import AsyncMock, MagicMock
import pytest
from flock.events.bus import EventBus
from flock.observability.aggregator import TelemetryAggregator
from flock.observability.models import MetricType
from flock.observability.registry import MetricsRegistry


@pytest.mark.asyncio
async def test_aggregator_listens_to_event_bus() -> None:
    registry = MetricsRegistry()
    events = EventBus()
    aggregator = TelemetryAggregator(registry, events)
    aggregator.start()

    # Emit raft commit event
    await events.publish("consensus.log.committed", {"term": 3})

    # Let event loop run tasks
    await asyncio.sleep(0.01)

    commits = registry.get_metric("flock.consensus.commits.total")
    assert commits is not None
    assert commits.value == 1.0

    term = registry.get_metric("flock.consensus.current_term")
    assert term is not None
    assert term.value == 3.0
