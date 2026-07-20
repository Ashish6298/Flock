"""Unit tests for SecurityService."""

import asyncio
from unittest.mock import MagicMock
import pytest
from flock.events.bus import EventBus
from flock.messaging.bus import MessageBus
from flock.protocol.packet import MessageType
from flock.security.models import NodeIdentity
from flock.security.service import SecurityService


@pytest.mark.asyncio
async def test_security_service_auth_handler() -> None:
    bus = MagicMock(spec=MessageBus)
    bus.router = MagicMock()
    events = EventBus()

    local_id = NodeIdentity(node_id="local", public_key="k1", certificate_pem="pem1")
    service = SecurityService("node-1", b"secret", local_id, bus, events)
    await service.start()

    service._bus.router.register.assert_called_once()
    args, kwargs = service._bus.router.register.call_args
    assert args[0] == MessageType.AUTH_REQUEST

    await service.stop()
