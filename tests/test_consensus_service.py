"""Integration tests for ConsensusService.

Tests cover:
* Service starts in FOLLOWER state
* Election timer starts on service.start()
* get_leader_id() returns None before election
* is_leader() returns False before election
* submit_command raises LeaderUnavailableError when not leader
* EventBus publishes consensus.leader.elected on election win
* EventBus publishes consensus.term.changed on term advance
* EventBus publishes consensus.log.committed on commit advance
* Message handler registration (8 Raft message types)
* Service stops cleanly, transitions back to FOLLOWER
* Single-node cluster auto-elects as leader
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Any, Dict, List

from flock.consensus.models import (
    AppendEntriesRequest,
    AppendEntriesResponse,
    ElectionResult,
    LogEntry,
    RaftRole,
    VoteRequest,
    VoteResponse,
)
from flock.consensus.service import ConsensusService
from flock.consensus.exceptions import LeaderUnavailableError
from flock.cluster.models import ClusterMember, ClusterMemberStatus
from flock.cluster.registry import MembershipRegistry
from flock.discovery.models import NodeDescription
from flock.events.bus import EventBus
from flock.messaging.bus import MessageBus
from flock.messaging.router import MessageRouter
from flock.protocol.packet import MessageType

import time


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_description(node_id: str = "node-1", port: int = 9200) -> NodeDescription:
    return NodeDescription(node_id=node_id, host="127.0.0.1", port=port)


def make_member(node_id: str = "node-1", port: int = 9200) -> ClusterMember:
    return ClusterMember(
        node_id=node_id,
        description=make_description(node_id, port),
        status=ClusterMemberStatus.ACTIVE,
        join_timestamp=time.time(),
    )


def make_registry_with_self(node_id: str = "node-1") -> MembershipRegistry:
    registry = MembershipRegistry()
    registry.add_member(make_member(node_id))
    return registry


def make_mock_bus() -> MagicMock:
    bus = MagicMock(spec=MessageBus)
    bus.send = AsyncMock()
    bus.router = MessageRouter()
    return bus


def make_service(
    node_id: str = "node-1",
    registry: MembershipRegistry | None = None,
    event_bus: EventBus | None = None,
    bus: MagicMock | None = None,
) -> ConsensusService:
    registry = registry or make_registry_with_self(node_id)
    event_bus = event_bus or EventBus()
    bus = bus or make_mock_bus()
    return ConsensusService(
        node_id=node_id,
        message_bus=bus,  # type: ignore[arg-type]
        event_bus=event_bus,
        membership_registry=registry,
        min_election_timeout=9999,  # prevent auto-fire
        max_election_timeout=9999,
    )


# ---------------------------------------------------------------------------
# Initial state
# ---------------------------------------------------------------------------

def test_initial_state_is_follower() -> None:
    service = make_service()
    assert service._sm.role == RaftRole.FOLLOWER
    assert service.is_leader() is False
    assert service.get_leader_id() is None


def test_initial_commit_index_is_zero() -> None:
    service = make_service()
    assert service.get_commit_index() == 0


def test_initial_term_is_zero() -> None:
    service = make_service()
    assert service.get_current_term() == 0


# ---------------------------------------------------------------------------
# Message handler registration
# ---------------------------------------------------------------------------

def test_all_raft_handlers_registered() -> None:
    bus = make_mock_bus()
    service = ConsensusService(
        node_id="node-1",
        message_bus=bus,  # type: ignore[arg-type]
        event_bus=EventBus(),
        membership_registry=make_registry_with_self(),
        min_election_timeout=9999,
        max_election_timeout=9999,
    )
    router = bus.router
    expected_types = [
        MessageType.RAFT_REQUEST_VOTE,
        MessageType.RAFT_VOTE_RESPONSE,
        MessageType.RAFT_APPEND_ENTRIES,
        MessageType.RAFT_APPEND_RESPONSE,
        MessageType.RAFT_HEARTBEAT,
        MessageType.RAFT_LEADER_ANNOUNCE,
        MessageType.RAFT_LOG_SYNC_REQUEST,
        MessageType.RAFT_LOG_SYNC_RESPONSE,
    ]
    for msg_type in expected_types:
        handler = router.get_handler(msg_type)
        assert handler is not None, f"Handler not registered for MessageType {msg_type}"


# ---------------------------------------------------------------------------
# submit_command
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_submit_command_raises_when_not_leader() -> None:
    service = make_service()
    with pytest.raises(LeaderUnavailableError):
        await service.submit_command(b"hello")


@pytest.mark.asyncio
async def test_submit_command_succeeds_when_leader() -> None:
    service = make_service()
    # Manually promote to leader
    service._sm.transition_to_candidate()
    service._sm.transition_to_leader()

    entry = await service.submit_command(b"test-command")

    assert entry.index == 1
    assert entry.term == 1
    assert entry.command == b"test-command"
    assert service._log.last_index == 1


@pytest.mark.asyncio
async def test_submit_command_sequential_entries() -> None:
    service = make_service()
    service._sm.transition_to_candidate()
    service._sm.transition_to_leader()

    e1 = await service.submit_command(b"cmd1")
    e2 = await service.submit_command(b"cmd2")

    assert e1.index == 1
    assert e2.index == 2


# ---------------------------------------------------------------------------
# Lifecycle
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_start_initialises_election_timer() -> None:
    service = make_service()
    await service.start()

    assert service._running is True
    assert service._election._timer_task is not None

    await service.stop()


@pytest.mark.asyncio
async def test_stop_cancels_timer_and_reverts_to_follower() -> None:
    service = make_service()
    await service.start()
    service._sm.transition_to_candidate()
    service._sm.transition_to_leader()

    await service.stop()

    assert service._running is False
    assert service._sm.role == RaftRole.FOLLOWER


# ---------------------------------------------------------------------------
# EventBus: leader elected
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_on_leader_elected_publishes_event() -> None:
    events = EventBus()
    published: list[Dict[str, Any]] = []

    async def capture(data: Dict[str, Any]) -> None:
        published.append(data)

    events.subscribe("consensus.leader.elected", capture)

    service = make_service(event_bus=events)

    result = ElectionResult(term=1, winner_id="node-1", votes_received=1, quorum_size=1)
    await service._on_leader_elected(result)

    assert len(published) == 1
    assert published[0]["leader_id"] == "node-1"
    assert published[0]["term"] == 1


# ---------------------------------------------------------------------------
# EventBus: term changed
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_higher_term_observed_publishes_term_changed() -> None:
    events = EventBus()
    term_events: list[Dict[str, Any]] = []

    async def capture(data: Dict[str, Any]) -> None:
        term_events.append(data)

    events.subscribe("consensus.term.changed", capture)

    service = make_service(event_bus=events)
    service._sm.transition_to_candidate()  # term = 1

    await service._on_higher_term_observed(5)

    assert len(term_events) == 1
    assert term_events[0]["new_term"] == 5


# ---------------------------------------------------------------------------
# Single-node cluster: auto election
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_single_node_cluster_wins_election_immediately() -> None:
    """A single-node cluster should become leader immediately on election trigger."""
    events = EventBus()
    elected_events: list[Dict[str, Any]] = []

    async def capture(data: Dict[str, Any]) -> None:
        elected_events.append(data)

    events.subscribe("consensus.leader.elected", capture)

    service = make_service(event_bus=events)
    service._election.set_peers([])  # no peers

    await service._election.trigger_election()

    assert service.is_leader() is True
    assert len(elected_events) >= 1


# ---------------------------------------------------------------------------
# EventBus: log committed (via replication)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_commit_advancement_publishes_committed_event() -> None:
    events = EventBus()
    committed: list[Dict[str, Any]] = []

    async def capture(data: Dict[str, Any]) -> None:
        committed.append(data)

    events.subscribe("consensus.log.committed", capture)

    service = make_service(event_bus=events)
    service._sm.transition_to_candidate()
    service._sm.transition_to_leader()

    await service.submit_command(b"data")

    # Simulate follower acknowledgement
    response = AppendEntriesResponse(
        follower_id="f1",
        term=service.get_current_term(),
        success=True,
        match_index=1,
    )
    service._replication.initialize_peer_indexes(["f1"])
    await service._replication.process_append_response(
        response, "f1", ["node-1", "f1"]
    )

    assert len(committed) == 1
    assert committed[0]["index"] == 1
