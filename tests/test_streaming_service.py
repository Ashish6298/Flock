"""Unit tests for StreamingService."""

import asyncio
from unittest.mock import MagicMock
import pytest
from flock.events.bus import EventBus
from flock.messaging.bus import MessageBus
from flock.protocol.packet import MessageType
from flock.storage.backend import StorageBackend
from flock.streaming.service import StreamingService


@pytest.mark.asyncio
async def test_streaming_service_handler_registration() -> None:
    bus = MagicMock(spec=MessageBus)
    bus.router = MagicMock()
    events = EventBus()
    storage = MagicMock(spec=StorageBackend)

    service = StreamingService("node-1", storage, bus, events)
    await service.start()

    service._bus.router.register.assert_called_once()
    args, kwargs = service._bus.router.register.call_args
    assert args[0] == MessageType.TOPIC_CREATE

    await service.stop()
