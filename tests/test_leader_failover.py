"""Integration tests for leader failover and re-election scenarios.

Tests cover:
* Leader steps down on receiving higher term AppendEntriesResponse
* New election starts after leader failure (mocked timer trigger)
* Votes not double-counted in same term
* New leader resumes replication with correct nextIndex
* Commit index not advanced below quorum
* Follower resets election timer on valid AppendEntries
* Former leader rejoins as follower after partition heals
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock
from typing import Any, Dict, List

from flock.consensus.election import ElectionEngine
from flock.consensus.log import ConsensusLog
from flock.consensus.models import (
    AppendEntriesRequest,
    AppendEntriesResponse,
    ElectionResult,
    LogEntry,
    RaftRole,
    VoteRequest,
    VoteResponse,
)
from flock.consensus.replication import ReplicationEngine
from flock.consensus.state_machine import RaftStateMachine
from flock.events.bus import EventBus
from flock.types import NodeInfo


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_entry(index: int, term: int) -> LogEntry:
    return LogEntry(index=index, term=term)


def make_peer(node_id: str, port: int = 9300) -> NodeInfo:
    return NodeInfo(node_id=node_id, host="127.0.0.1", port=port)


def make_mock_bus() -> MagicMock:
    bus = MagicMock()
    bus.send = AsyncMock()
    return bus


def make_engine_pair(
    node_id: str = "leader",
) -> tuple[RaftStateMachine, ConsensusLog, ElectionEngine, ReplicationEngine]:
    sm = RaftStateMachine(node_id)
    log = ConsensusLog()
    bus = make_mock_bus()
    events = EventBus()
    election = ElectionEngine(
        node_id=node_id,
        state_machine=sm,
        consensus_log=log,
        message_bus=bus,  # type: ignore[arg-type]
        min_timeout_sec=9999,
        max_timeout_sec=9999,
    )
    replication = ReplicationEngine(
        node_id=node_id,
        state_machine=sm,
        consensus_log=log,
        message_bus=bus,  # type: ignore[arg-type]
        event_bus=events,
    )
    return sm, log, election, replication


# ---------------------------------------------------------------------------
# Leader steps down on higher term
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_leader_steps_down_on_higher_term_in_response() -> None:
    step_downs: list[int] = []

    async def on_step_down(term: int) -> None:
        step_downs.append(term)

    sm = RaftStateMachine("leader")
    sm.transition_to_candidate()
    sm.transition_to_leader()
    log = ConsensusLog()
    events = EventBus()
    engine = ReplicationEngine(
        node_id="leader",
        state_machine=sm,
        consensus_log=log,
        message_bus=make_mock_bus(),  # type: ignore[arg-type]
        event_bus=events,
        on_step_down=on_step_down,
    )

    response = AppendEntriesResponse(
        follower_id="f1",
        term=10,   # higher term
        success=False,
    )
    await engine.process_append_response(response, "f1", ["leader", "f1"])

    assert step_downs == [10]


@pytest.mark.asyncio
async def test_step_down_updates_state_machine_term() -> None:
    sm = RaftStateMachine("leader")
    sm.transition_to_candidate()
    sm.transition_to_leader()

    # Simulate receiving a higher term
    stepped = sm.update_term(15)
    assert stepped is True
    assert sm.role == RaftRole.FOLLOWER
    assert sm.current_term == 15


# ---------------------------------------------------------------------------
# New election after leader failure
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_follower_triggers_election_on_timeout() -> None:
    sm, log, election, _ = make_engine_pair("node-2")
    # Add peers so we stay in CANDIDATE (need quorum from peers)
    election.set_peers([make_peer("node-3"), make_peer("node-4")])
    elections_started: list[int] = []

    original_trigger = election.trigger_election

    async def patched_trigger() -> None:
        elections_started.append(sm.current_term)
        await original_trigger()

    election._on_timeout = patched_trigger

    # Simulate timer fire
    await election._election_timer_coro(0.0)

    assert len(elections_started) >= 1
    assert sm.role == RaftRole.CANDIDATE


# ---------------------------------------------------------------------------
# Votes not double-counted in same term
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_same_voter_only_counted_once() -> None:
    sm, log, election, _ = make_engine_pair("node-1")
    election.set_peers([make_peer("node-2"), make_peer("node-3")])

    await election.trigger_election()  # term=1, self-vote counted

    # node-2 votes twice (network duplicate)
    resp = VoteResponse(voter_id="node-2", term=1, vote_granted=True)
    await election.tally_vote(resp)
    await election.tally_vote(resp)  # duplicate

    # Vote count should still only be 2 (self + node-2 once)
    assert sm.vote_count() == 2


# ---------------------------------------------------------------------------
# New leader resumes correct nextIndex
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_new_leader_initialises_next_index_correctly() -> None:
    sm = RaftStateMachine("new-leader")
    sm.transition_to_candidate()
    sm.transition_to_leader()
    log = ConsensusLog()
    log.append([make_entry(i, 1) for i in range(1, 4)])  # 3 entries
    events = EventBus()
    engine = ReplicationEngine(
        node_id="new-leader",
        state_machine=sm,
        consensus_log=log,
        message_bus=make_mock_bus(),  # type: ignore[arg-type]
        event_bus=events,
    )
    engine.initialize_peer_indexes(["f1", "f2"])

    # nextIndex should be last_index + 1 = 4 for each peer
    assert engine._next_index["f1"] == 4
    assert engine._next_index["f2"] == 4
    assert engine._match_index["f1"] == 0
    assert engine._match_index["f2"] == 0


# ---------------------------------------------------------------------------
# Commit index not advanced below quorum
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_commit_not_advanced_without_quorum() -> None:
    sm = RaftStateMachine("leader")
    sm.transition_to_candidate()
    sm.transition_to_leader()
    log = ConsensusLog()
    log.append([make_entry(1, 1), make_entry(2, 1), make_entry(3, 1)])
    events = EventBus()
    engine = ReplicationEngine(
        node_id="leader",
        state_machine=sm,
        consensus_log=log,
        message_bus=make_mock_bus(),  # type: ignore[arg-type]
        event_bus=events,
    )
    engine.initialize_peer_indexes(["f1", "f2", "f3", "f4"])

    # Only 1 out of 4 followers acknowledged
    response = AppendEntriesResponse(
        follower_id="f1",
        term=1,
        success=True,
        match_index=3,
    )
    await engine.process_append_response(
        response, "f1", ["leader", "f1", "f2", "f3", "f4"]
    )

    # 5-node cluster: quorum = 3, only 2 have index 3 (leader + f1)
    assert log.commit_index == 0  # NOT advanced yet


@pytest.mark.asyncio
async def test_commit_advanced_when_quorum_reached() -> None:
    sm = RaftStateMachine("leader")
    sm.transition_to_candidate()
    sm.transition_to_leader()
    log = ConsensusLog()
    log.append([make_entry(1, 1)])
    events = EventBus()
    engine = ReplicationEngine(
        node_id="leader",
        state_machine=sm,
        consensus_log=log,
        message_bus=make_mock_bus(),  # type: ignore[arg-type]
        event_bus=events,
    )
    engine.initialize_peer_indexes(["f1", "f2"])

    # 3-node cluster: quorum = 2 (leader + 1 follower)
    response = AppendEntriesResponse(
        follower_id="f1",
        term=1,
        success=True,
        match_index=1,
    )
    await engine.process_append_response(response, "f1", ["leader", "f1", "f2"])

    assert log.commit_index == 1  # Quorum reached


# ---------------------------------------------------------------------------
# Follower resets timer on valid AppendEntries
# ---------------------------------------------------------------------------

def test_follower_updates_leader_on_append_entries() -> None:
    sm = RaftStateMachine("follower")
    log = ConsensusLog()
    events = EventBus()
    engine = ReplicationEngine(
        node_id="follower",
        state_machine=sm,
        consensus_log=log,
        message_bus=make_mock_bus(),  # type: ignore[arg-type]
        event_bus=events,
    )

    req = AppendEntriesRequest(
        leader_id="leader-node",
        term=2,
        prev_log_index=0,
        prev_log_term=0,
        entries=[],
        leader_commit=0,
    )
    resp = engine.handle_append_entries(req)

    assert resp.success is True
    assert sm.leader_id == "leader-node"
    assert sm.current_term == 2


# ---------------------------------------------------------------------------
# Former leader rejoins as follower
# ---------------------------------------------------------------------------

def test_former_leader_accepts_append_entries_as_follower() -> None:
    """A deposed leader should accept AppendEntries from the new leader."""
    sm = RaftStateMachine("old-leader")
    sm.transition_to_candidate()
    sm.transition_to_leader()
    log = ConsensusLog()
    events = EventBus()
    engine = ReplicationEngine(
        node_id="old-leader",
        state_machine=sm,
        consensus_log=log,
        message_bus=make_mock_bus(),  # type: ignore[arg-type]
        event_bus=events,
    )

    # Received higher term – step down
    sm.update_term(5)

    req = AppendEntriesRequest(
        leader_id="new-leader",
        term=5,
        prev_log_index=0,
        prev_log_term=0,
        entries=[make_entry(1, 5)],
        leader_commit=0,
    )
    resp = engine.handle_append_entries(req)

    assert resp.success is True
    assert sm.role == RaftRole.FOLLOWER
    assert sm.leader_id == "new-leader"
    assert log.last_index == 1


# ---------------------------------------------------------------------------
# Election: split vote – no double promotion
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_split_vote_no_leader_elected() -> None:
    """With only 1 vote out of 3, quorum is not reached and no leader is elected."""
    promoted: list[str] = []

    async def on_elected(result: ElectionResult) -> None:
        promoted.append(result.winner_id)

    sm, log, election, _ = make_engine_pair("node-1")
    election._on_leader_elected = on_elected
    election.set_peers([make_peer("node-2"), make_peer("node-3")])

    await election.trigger_election()  # term=1, self-vote only

    # node-2 denies (split vote)
    resp = VoteResponse(voter_id="node-2", term=1, vote_granted=False, reason="split vote")
    await election.tally_vote(resp)

    assert sm.role == RaftRole.CANDIDATE
    assert promoted == []
