"""Unit tests for FederationService."""

import asyncio
from unittest.mock import MagicMock
import pytest
from flock.events.bus import EventBus
from flock.messaging.bus import MessageBus
from flock.protocol.packet import MessageType
from flock.federation.service import FederationService


@pytest.mark.asyncio
async def test_federation_service_join_handler() -> None:
    bus = MagicMock(spec=MessageBus)
    bus.router = MagicMock()
    events = EventBus()

    service = FederationService("cluster-a", bus, events)
    await service.start()

    service._bus.router.register.assert_called_once()
    args, kwargs = service._bus.router.register.call_args
    assert args[0] == MessageType.FEDERATION_JOIN_REQUEST

    await service.stop()
