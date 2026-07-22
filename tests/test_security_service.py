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
    service = SecurityService("node-1", b"secret_key_16bytes", local_id, bus, events)
    await service.start()

    assert service._bus.router.register.call_count == 3
    registered_types = [args[0] for args, _ in service._bus.router.register.call_args_list]
    assert MessageType.AUTH_REQUEST in registered_types
    assert MessageType.SECRET_RETRIEVAL_REQUEST in registered_types
    assert MessageType.SECURITY_POLICY_SYNC in registered_types

    await service.stop()
