"""Unit tests for WorkflowService."""

import asyncio
from unittest.mock import MagicMock
import pytest
from flock.events.bus import EventBus
from flock.messaging.bus import MessageBus
from flock.protocol.packet import MessageType
from flock.storage.backend import StorageBackend
from flock.workflow.service import WorkflowService


@pytest.mark.asyncio
async def test_workflow_service_submission_handler() -> None:
    bus = MagicMock(spec=MessageBus)
    bus.router = MagicMock()
    events = EventBus()
    storage = MagicMock(spec=StorageBackend)

    service = WorkflowService("node-1", storage, bus, events)
    await service.start()

    service._bus.router.register.assert_called_once()
    args, kwargs = service._bus.router.register.call_args
    assert args[0] == MessageType.WORKFLOW_SUBMIT

    await service.stop()
