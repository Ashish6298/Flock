"""Unit tests for SchedulingService."""

import asyncio
from unittest.mock import MagicMock
import pytest
from flock.events.bus import EventBus
from flock.messaging.bus import MessageBus
from flock.protocol.packet import MessageType
from flock.scheduling.service import SchedulingService


@pytest.mark.asyncio
async def test_scheduler_service_handler_registration() -> None:
    bus = MagicMock(spec=MessageBus)
    bus.router = MagicMock()
    events = EventBus()

    service = SchedulingService("node-1", bus, events)
    await service.start()

    service._bus.router.register.assert_called_once()
    args, kwargs = service._bus.router.register.call_args
    assert args[0] == MessageType.SCHEDULE_CREATE

    await service.stop()
