"""Unit tests for ObservabilityService."""

import asyncio
from unittest.mock import AsyncMock, MagicMock
import pytest
from flock.events.bus import EventBus
from flock.messaging.bus import MessageBus
from flock.protocol.packet import MessageType
from flock.observability.service import ObservabilityService


@pytest.mark.asyncio
async def test_observability_service_metrics_endpoint() -> None:
    bus = MagicMock(spec=MessageBus)
    bus.router = MagicMock()
    events = EventBus()

    service = ObservabilityService("node-1", bus, events)
    await service.start()

    # Verify metric registration handler was registered on bus router
    service._bus.router.register.assert_called_once()
    args, kwargs = service._bus.router.register.call_args
    assert args[0] == MessageType.METRICS_REQUEST

    await service.stop()
