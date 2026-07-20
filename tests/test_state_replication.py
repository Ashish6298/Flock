"""Unit tests validating state replication pipeline under simulated network commits."""

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
async def test_replicated_pipeline_integration() -> None:
    # Build two nodes (representing a replication channel)
    events_leader = EventBus()
    events_follower = EventBus()

    consensus_leader = MagicMock(spec=ConsensusService)
    consensus_leader.is_leader.return_value = True
    consensus_leader.submit_command = AsyncMock()
    consensus_leader._log = MagicMock()

    consensus_follower = MagicMock(spec=ConsensusService)
    consensus_follower.is_leader.return_value = False
    consensus_follower._log = MagicMock()

    leader_service = StateMachineService("leader", consensus_leader, events_leader)
    follower_service = StateMachineService("follower", consensus_follower, events_follower)

    await leader_service.start()
    await follower_service.start()

    cmd = StateCommand(
        command_id="cmd-repl-1",
        operation=StateOperation.PUT,
        key="cluster_mode",
        value="p2p",
        timestamp=time.time(),
    )
    cmd_bytes = json.dumps(cmd.model_dump()).encode("utf-8")

    # When leader submits command, it waits for 'state.command.applied' locally.
    # We simulate the commit pipeline on the leader:
    async def simulate_leader_commit() -> None:
        await asyncio.sleep(0.02)
        # Log is updated
        entry = LogEntry(index=1, term=1, command=cmd_bytes)
        consensus_leader._log.get_entry.return_value = entry
        await events_leader.publish("consensus.log.committed", {"index": 1, "term": 1})

    asyncio.create_task(simulate_leader_commit())

    # Submit command on leader
    res = await leader_service.submit_command(cmd)
    assert res.value == "p2p"
    assert leader_service.get("cluster_mode").value == "p2p"

    # Now simulate the replication over the wire to the follower:
    entry = LogEntry(index=1, term=1, command=cmd_bytes)
    consensus_follower._log.get_entry.return_value = entry
    await events_follower.publish("consensus.log.committed", {"index": 1, "term": 1})

    # Follower should have applied it automatically
    assert follower_service.get("cluster_mode").value == "p2p"
    assert follower_service.exists("cluster_mode") is True

    await leader_service.stop()
    await follower_service.stop()
