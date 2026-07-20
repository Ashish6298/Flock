"""Unit tests for StateMachineService."""

import asyncio
import json
import time
from unittest.mock import AsyncMock, MagicMock
import pytest
from flock.consensus.service import ConsensusService
from flock.consensus.models import LogEntry
from flock.events.bus import EventBus
from flock.statemachine.exceptions import StateMachineError
from flock.statemachine.models import StateCommand, StateOperation
from flock.statemachine.service import StateMachineService


@pytest.mark.asyncio
async def test_service_submit_command_replicated() -> None:
    # Set up mocks for ConsensusService
    consensus = MagicMock(spec=ConsensusService)
    consensus.is_leader.return_value = True
    consensus.submit_command = AsyncMock()
    # Mock log structure
    consensus._log = MagicMock()

    events = EventBus()
    service = StateMachineService(
        node_id="leader-node",
        consensus_service=consensus,
        event_bus=events,
    )
    await service.start()

    cmd = StateCommand(
        command_id="cmd-abc",
        operation=StateOperation.PUT,
        key="score",
        value=99,
        timestamp=time.time(),
    )

    # We need to simulate that another task or the consensus loop will apply the entry.
    # We set up an async task that waits briefly and then fires the apply_committed_entry
    # as if consensus callback triggered it.
    async def simulate_consensus_apply() -> None:
        await asyncio.sleep(0.05)
        # Emulate consensus commit event publishing
        entry = LogEntry(index=1, term=1, command=json.dumps(cmd.model_dump()).encode("utf-8"))
        consensus._log.get_entry.return_value = entry
        await events.publish("consensus.log.committed", {"index": 1, "term": 1})

    asyncio.create_task(simulate_consensus_apply())

    # Call submit_command which awaits the EventBus notification of applied command
    result = await service.submit_command(cmd)
    assert result.value == 99
    assert service.get("score").value == 99

    await service.stop()
