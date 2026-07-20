"""Unit tests for OrchestratorService."""

import asyncio
from unittest.mock import MagicMock
import pytest
from flock.events.bus import EventBus
from flock.messaging.bus import MessageBus
from flock.protocol.packet import MessageType
from flock.orchestrator.models import ClusterPolicy
from flock.orchestrator.service import OrchestratorService


@pytest.mark.asyncio
async def test_orchestrator_service_policy_sync() -> None:
    bus = MagicMock(spec=MessageBus)
    bus.router = MagicMock()
    events = EventBus()

    policy = ClusterPolicy(
        policy_id="pol-1",
        strategy_name="balanced",
    )

    service = OrchestratorService("node-1", bus, events, policy)
    await service.start()

    service._bus.router.register.assert_called_once()
    args, kwargs = service._bus.router.register.call_args
    assert args[0] == MessageType.ORCHESTRATOR_POLICY_SYNC

    await service.stop()
