"""Unit tests for ReplicationEngine – AppendEntries RPC logic.

Tests cover:
* Successful handle_append_entries appends entries
* Rejection when prev_log_index/term mismatch (conflict hint returned)
* Truncation of conflicting suffix before appending new entries
* Heartbeat (empty entries) accepted without modifying log
* Commit index advanced from leader_commit in AppendEntries
* Stale term in AppendEntries triggers rejection (not step-down; caller handles)
* calculate_commit_index for various matchIndex distributions
* process_append_response advances matchIndex and triggers commit
* process_append_response decrements nextIndex on failure
* Higher term in AppendEntriesResponse triggers on_step_down callback
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock

from flock.consensus.log import ConsensusLog
from flock.consensus.models import (
    AppendEntriesRequest,
    AppendEntriesResponse,
    LogEntry,
    RaftRole,
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


def make_peer(node_id: str, port: int = 9100) -> NodeInfo:
    return NodeInfo(node_id=node_id, host="127.0.0.1", port=port)


def make_leader_sm(term: int = 1) -> RaftStateMachine:
    sm = RaftStateMachine("leader")
    sm.transition_to_candidate()     # term → 1
    sm.transition_to_leader()
    if term > 1:
        sm.update_term(term - 1)
        sm.transition_to_candidate()
        sm.transition_to_leader()
    return sm


def make_follower_sm(term: int = 1) -> RaftStateMachine:
    sm = RaftStateMachine("follower")
    sm.update_term(term) if term > 0 else None
    return sm


def make_engine(
    node_id: str = "follower",
    sm: RaftStateMachine | None = None,
    log: ConsensusLog | None = None,
    event_bus: EventBus | None = None,
    on_step_down: AsyncMock | None = None,
) -> ReplicationEngine:
    _sm = sm if sm is not None else RaftStateMachine(node_id)
    _log = log if log is not None else ConsensusLog()
    bus = MagicMock()
    bus.send = AsyncMock()
    events = event_bus if event_bus is not None else EventBus()
    return ReplicationEngine(
        node_id=node_id,
        state_machine=_sm,
        consensus_log=_log,
        message_bus=bus,  # type: ignore[arg-type]
        event_bus=events,
        on_step_down=on_step_down,
    )


# ---------------------------------------------------------------------------
# handle_append_entries: basic acceptance
# ---------------------------------------------------------------------------

def test_handle_ae_accepts_valid_entries() -> None:
    sm = RaftStateMachine("follower")
    log = ConsensusLog()
    engine = make_engine("follower", sm=sm, log=log)

    req = AppendEntriesRequest(
        leader_id="leader",
        term=1,
        prev_log_index=0,
        prev_log_term=0,
        entries=[make_entry(1, 1), make_entry(2, 1)],
        leader_commit=0,
    )
    resp = engine.handle_append_entries(req)

    assert resp.success is True
    assert resp.match_index == 2
    assert log.last_index == 2


def test_handle_ae_heartbeat_no_entries() -> None:
    """Empty entries (heartbeat) should succeed without modifying log."""
    sm = RaftStateMachine("follower")
    log = ConsensusLog()
    log.append([make_entry(1, 1)])
    engine = make_engine("follower", sm=sm, log=log)

    req = AppendEntriesRequest(
        leader_id="leader",
        term=1,
        prev_log_index=1,
        prev_log_term=1,
        entries=[],
        leader_commit=0,
    )
    resp = engine.handle_append_entries(req)

    assert resp.success is True
    assert log.last_index == 1  # unchanged


def test_handle_ae_advances_commit_index() -> None:
    sm = RaftStateMachine("follower")
    log = ConsensusLog()
    log.append([make_entry(1, 1), make_entry(2, 1)])
    engine = make_engine("follower", sm=sm, log=log)

    req = AppendEntriesRequest(
        leader_id="leader",
        term=1,
        prev_log_index=2,
        prev_log_term=1,
        entries=[],
        leader_commit=2,  # leader says commit up to 2
    )
    resp = engine.handle_append_entries(req)

    assert resp.success is True
    assert log.commit_index == 2


# ---------------------------------------------------------------------------
# handle_append_entries: rejection cases
# ---------------------------------------------------------------------------

def test_handle_ae_rejects_stale_term() -> None:
    sm = RaftStateMachine("follower")
    sm.update_term(5)  # current_term = 5
    log = ConsensusLog()
    engine = make_engine("follower", sm=sm, log=log)

    req = AppendEntriesRequest(
        leader_id="leader",
        term=3,  # stale
        prev_log_index=0,
        prev_log_term=0,
        entries=[],
        leader_commit=0,
    )
    resp = engine.handle_append_entries(req)

    assert resp.success is False
    assert resp.term == 5


def test_handle_ae_rejects_prev_log_mismatch() -> None:
    sm = RaftStateMachine("follower")
    log = ConsensusLog()
    log.append([make_entry(1, 1)])  # term=1 at index 1
    engine = make_engine("follower", sm=sm, log=log)

    req = AppendEntriesRequest(
        leader_id="leader",
        term=2,
        prev_log_index=1,
        prev_log_term=2,  # mismatch: local is term=1
        entries=[make_entry(2, 2)],
        leader_commit=0,
    )
    resp = engine.handle_append_entries(req)

    assert resp.success is False
    assert resp.conflict_index > 0


def test_handle_ae_rejects_prev_log_beyond_local() -> None:
    sm = RaftStateMachine("follower")
    log = ConsensusLog()
    engine = make_engine("follower", sm=sm, log=log)

    # Follower has empty log, leader thinks prev_log_index=3
    req = AppendEntriesRequest(
        leader_id="leader",
        term=1,
        prev_log_index=3,
        prev_log_term=1,
        entries=[make_entry(4, 1)],
        leader_commit=0,
    )
    resp = engine.handle_append_entries(req)

    assert resp.success is False
    assert resp.conflict_index >= 1


# ---------------------------------------------------------------------------
# handle_append_entries: conflict repair (truncation)
# ---------------------------------------------------------------------------

def test_handle_ae_truncates_conflicting_suffix() -> None:
    """Follower has conflicting entries; leader's entries should win."""
    sm = RaftStateMachine("follower")
    log = ConsensusLog()
    # Follower has entries at term 1
    log.append([make_entry(1, 1), make_entry(2, 1), make_entry(3, 1)])
    engine = make_engine("follower", sm=sm, log=log)

    # Leader sends entries starting at index 2 but with term 2 (different)
    req = AppendEntriesRequest(
        leader_id="leader",
        term=2,
        prev_log_index=1,
        prev_log_term=1,
        entries=[make_entry(2, 2), make_entry(3, 2)],  # different term
        leader_commit=0,
    )
    resp = engine.handle_append_entries(req)

    assert resp.success is True
    assert log.last_index == 3
    # Entry at index 2 should now be term 2
    assert log.get_entry(2) is not None
    assert log.get_entry(2).term == 2  # type: ignore[union-attr]


def test_handle_ae_idempotent_same_entries() -> None:
    """Receiving the same entries twice should not duplicate."""
    sm = RaftStateMachine("follower")
    log = ConsensusLog()
    engine = make_engine("follower", sm=sm, log=log)

    entries = [make_entry(1, 1), make_entry(2, 1)]
    req = AppendEntriesRequest(
        leader_id="leader",
        term=1,
        prev_log_index=0,
        prev_log_term=0,
        entries=entries,
        leader_commit=0,
    )
    engine.handle_append_entries(req)
    resp2 = engine.handle_append_entries(req)  # send again

    assert resp2.success is True
    assert log.last_index == 2  # no duplicate


# ---------------------------------------------------------------------------
# calculate_commit_index
# ---------------------------------------------------------------------------

def test_calculate_commit_index_quorum_case() -> None:
    # 3-node cluster: leader(3) + follower1(3) + follower2(2)
    # quorum = 2 out of 3
    idx = ReplicationEngine.calculate_commit_index(
        match_indexes={"f1": 3, "f2": 2},
        self_index=3,
        current_term=1,
    )
    # 3 nodes, quorum=2, all indexes [3,3,2] sorted desc → [3,3,2]
    # quorum-th = index 2 → value 3
    assert idx == 3


def test_calculate_commit_index_no_quorum() -> None:
    # Only leader has entries; followers at 0
    idx = ReplicationEngine.calculate_commit_index(
        match_indexes={"f1": 0, "f2": 0},
        self_index=5,
        current_term=1,
    )
    # [5,0,0] sorted desc → [5,0,0], quorum-th (2nd) = 0
    assert idx == 0


def test_calculate_commit_index_all_caught_up() -> None:
    idx = ReplicationEngine.calculate_commit_index(
        match_indexes={"f1": 7, "f2": 7, "f3": 7, "f4": 7},
        self_index=7,
        current_term=1,
    )
    assert idx == 7


def test_calculate_commit_index_single_node() -> None:
    idx = ReplicationEngine.calculate_commit_index(
        match_indexes={},
        self_index=4,
        current_term=1,
    )
    assert idx == 4


# ---------------------------------------------------------------------------
# process_append_response
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_process_append_response_success_advances_match_index() -> None:
    sm = make_leader_sm(term=1)
    log = ConsensusLog()
    log.append([make_entry(1, 1), make_entry(2, 1), make_entry(3, 1)])
    events = EventBus()
    engine = make_engine("leader", sm=sm, log=log, event_bus=events)
    engine.initialize_peer_indexes(["f1", "f2"])

    response = AppendEntriesResponse(
        follower_id="f1",
        term=1,
        success=True,
        match_index=3,
    )
    await engine.process_append_response(response, "f1", ["leader", "f1", "f2"])

    assert engine._match_index["f1"] == 3
    assert engine._next_index["f1"] == 4


@pytest.mark.asyncio
async def test_process_append_response_failure_decrements_next_index() -> None:
    sm = make_leader_sm(term=1)
    log = ConsensusLog()
    events = EventBus()
    engine = make_engine("leader", sm=sm, log=log, event_bus=events)
    engine.initialize_peer_indexes(["f1"])

    response = AppendEntriesResponse(
        follower_id="f1",
        term=1,
        success=False,
        conflict_index=2,
    )
    await engine.process_append_response(response, "f1", ["leader", "f1"])

    assert engine._next_index["f1"] == 2  # backed to conflict_index


@pytest.mark.asyncio
async def test_process_append_response_higher_term_triggers_step_down() -> None:
    step_down_calls: list[int] = []

    async def on_step_down(term: int) -> None:
        step_down_calls.append(term)

    sm = make_leader_sm(term=1)
    log = ConsensusLog()
    events = EventBus()
    engine = make_engine("leader", sm=sm, log=log, event_bus=events, on_step_down=on_step_down)

    response = AppendEntriesResponse(
        follower_id="f1",
        term=99,   # higher term
        success=False,
    )
    await engine.process_append_response(response, "f1", ["leader", "f1"])

    assert step_down_calls == [99]


@pytest.mark.asyncio
async def test_process_append_response_publishes_committed_event() -> None:
    committed_events: list[dict] = []

    async def on_committed(data: dict) -> None:
        committed_events.append(data)

    sm = make_leader_sm(term=1)
    log = ConsensusLog()
    log.append([make_entry(1, 1)])
    events = EventBus()
    events.subscribe("consensus.log.committed", on_committed)
    engine = make_engine("leader", sm=sm, log=log, event_bus=events)
    engine.initialize_peer_indexes(["f1"])

    # f1 acknowledges index 1
    response = AppendEntriesResponse(
        follower_id="f1",
        term=1,
        success=True,
        match_index=1,
    )
    await engine.process_append_response(response, "f1", ["leader", "f1"])

    assert len(committed_events) == 1
    assert committed_events[0]["index"] == 1
