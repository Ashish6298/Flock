"""Unit tests for ResourceManagementService."""

import asyncio
from unittest.mock import MagicMock
import pytest
from flock.events.bus import EventBus
from flock.messaging.bus import MessageBus
from flock.protocol.packet import MessageType
from flock.resources.service import ResourceManagementService


@pytest.mark.asyncio
async def test_resource_service_allocation_handler() -> None:
    bus = MagicMock(spec=MessageBus)
    bus.router = MagicMock()
    events = EventBus()

    service = ResourceManagementService("node-1", bus, events)
    await service.start()

    service._bus.router.register.assert_called_once()
    args, kwargs = service._bus.router.register.call_args
    assert args[0] == MessageType.ALLOCATION_REQUEST

    await service.stop()
