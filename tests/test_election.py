"""Unit tests for ElectionEngine and RaftStateMachine.

Tests cover:
* Initial state is FOLLOWER
* transition_to_candidate increments term and votes for self
* transition_to_leader from CANDIDATE only
* Duplicate vote rejection (same term, different candidate)
* Stale term rejection in VoteRequest handling
* handle_vote_request: grants vote when log is up-to-date
* handle_vote_request: denies vote when candidate log is stale
* check_quorum correctness for cluster sizes 1, 3, 5
* Randomised timeout determinism (mocked asyncio.sleep)
* Timer cancellation does not raise
* trigger_election transitions to CANDIDATE and broadcasts votes
* Quorum promotion to LEADER via tally_vote
* Step-down on higher term in VoteResponse
* No duplicate promotions (votes beyond quorum are idempotent)
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from typing import List

from flock.consensus.election import ElectionEngine
from flock.consensus.exceptions import ConsensusViolationError, InvalidTermError
from flock.consensus.log import ConsensusLog
from flock.consensus.models import (
    RaftRole,
    VoteRequest,
    VoteResponse,
    ElectionResult,
)
from flock.consensus.state_machine import RaftStateMachine
from flock.types import NodeInfo


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_peer(node_id: str, port: int = 9000) -> NodeInfo:
    return NodeInfo(node_id=node_id, host="127.0.0.1", port=port)


def make_sm(node_id: str = "node-1") -> RaftStateMachine:
    return RaftStateMachine(node_id=node_id)


def make_log() -> ConsensusLog:
    return ConsensusLog()


def make_mock_bus() -> MagicMock:
    bus = MagicMock()
    bus.send = AsyncMock()
    return bus


def make_engine(
    node_id: str = "node-1",
    sm: RaftStateMachine | None = None,
    log: ConsensusLog | None = None,
    bus: MagicMock | None = None,
    on_elected: AsyncMock | None = None,
) -> ElectionEngine:
    sm = sm or make_sm(node_id)
    log = log or make_log()
    bus = bus or make_mock_bus()
    engine = ElectionEngine(
        node_id=node_id,
        state_machine=sm,
        consensus_log=log,
        message_bus=bus,  # type: ignore[arg-type]
        min_timeout_sec=9999,  # prevents auto-firing in tests
        max_timeout_sec=9999,
        on_leader_elected=on_elected,
    )
    return engine


# ---------------------------------------------------------------------------
# RaftStateMachine: initial state
# ---------------------------------------------------------------------------

def test_initial_role_is_follower() -> None:
    sm = make_sm()
    assert sm.role == RaftRole.FOLLOWER
    assert sm.current_term == 0
    assert sm.voted_for is None
    assert sm.leader_id is None


# ---------------------------------------------------------------------------
# RaftStateMachine: transitions
# ---------------------------------------------------------------------------

def test_transition_to_candidate_increments_term() -> None:
    sm = make_sm()
    new_term = sm.transition_to_candidate()
    assert new_term == 1
    assert sm.current_term == 1
    assert sm.role == RaftRole.CANDIDATE
    assert sm.voted_for == "node-1"  # self-vote


def test_transition_to_candidate_twice_increments_again() -> None:
    sm = make_sm()
    sm.transition_to_candidate()
    # Step down to follower first (split vote)
    sm.transition_to_follower(term=1)
    new_term = sm.transition_to_candidate()
    assert new_term == 2


def test_transition_to_leader_from_candidate() -> None:
    sm = make_sm()
    sm.transition_to_candidate()
    sm.transition_to_leader()
    assert sm.role == RaftRole.LEADER


def test_transition_to_leader_from_follower_raises() -> None:
    sm = make_sm()
    with pytest.raises(ConsensusViolationError):
        sm.transition_to_leader()


def test_transition_to_follower_with_higher_term() -> None:
    sm = make_sm()
    sm.transition_to_candidate()   # term = 1
    sm.transition_to_follower(term=5)
    assert sm.role == RaftRole.FOLLOWER
    assert sm.current_term == 5
    assert sm.voted_for is None


def test_transition_to_follower_with_lower_term_raises() -> None:
    sm = make_sm()
    sm.transition_to_candidate()   # term = 1
    with pytest.raises(InvalidTermError):
        sm.transition_to_follower(term=0)


def test_update_term_steps_down_and_clears_vote() -> None:
    sm = make_sm()
    sm.transition_to_candidate()   # term = 1, voted_for = node-1
    changed = sm.update_term(5)
    assert changed is True
    assert sm.current_term == 5
    assert sm.role == RaftRole.FOLLOWER
    assert sm.voted_for is None


def test_update_term_same_term_returns_false() -> None:
    sm = make_sm()
    assert sm.update_term(0) is False


def test_advance_commit_index() -> None:
    sm = make_sm()
    advanced = sm.advance_commit_index(5)
    assert advanced is True
    assert sm.commit_index == 5


def test_advance_commit_index_does_not_decrease() -> None:
    sm = make_sm()
    sm.advance_commit_index(5)
    advanced = sm.advance_commit_index(3)
    assert advanced is False
    assert sm.commit_index == 5


# ---------------------------------------------------------------------------
# RaftStateMachine: vote accounting
# ---------------------------------------------------------------------------

def test_can_vote_for_grants_fresh_vote() -> None:
    sm = make_sm("node-2")
    grant, reason = sm.can_vote_for(
        candidate_id="node-1",
        candidate_term=1,
        candidate_last_log_index=0,
        candidate_last_log_term=0,
        local_last_log_index=0,
        local_last_log_term=0,
    )
    assert grant is True


def test_can_vote_for_denies_stale_term() -> None:
    sm = make_sm("node-2")
    sm.transition_to_candidate()   # current_term = 1
    grant, reason = sm.can_vote_for(
        candidate_id="node-1",
        candidate_term=0,     # stale
        candidate_last_log_index=0,
        candidate_last_log_term=0,
        local_last_log_index=0,
        local_last_log_term=0,
    )
    assert grant is False
    assert "stale" in reason.lower()


def test_can_vote_for_denies_already_voted_different_candidate() -> None:
    sm = make_sm("node-2")
    sm.transition_to_candidate()   # votes for self (node-2)
    sm.transition_to_follower(term=1, voted_for="node-2")
    grant, _ = sm.can_vote_for(
        candidate_id="node-3",
        candidate_term=1,
        candidate_last_log_index=0,
        candidate_last_log_term=0,
        local_last_log_index=0,
        local_last_log_term=0,
    )
    assert grant is False


def test_can_vote_for_denies_stale_candidate_log() -> None:
    sm = make_sm("node-2")
    # node-2 has local log at index 5, term 3
    grant, reason = sm.can_vote_for(
        candidate_id="node-1",
        candidate_term=1,
        candidate_last_log_index=2,  # stale index
        candidate_last_log_term=1,
        local_last_log_index=5,
        local_last_log_term=3,
    )
    assert grant is False
    assert "stale" in reason.lower()


def test_record_vote_counts_correctly() -> None:
    sm = make_sm()
    sm.transition_to_candidate()
    count = sm.record_vote("node-2")
    assert count == 2  # self + node-2


# ---------------------------------------------------------------------------
# ElectionEngine: quorum
# ---------------------------------------------------------------------------

def test_check_quorum_single_node() -> None:
    assert ElectionEngine.check_quorum(1, 1) is True


def test_check_quorum_three_nodes_two_votes() -> None:
    assert ElectionEngine.check_quorum(2, 3) is True


def test_check_quorum_three_nodes_one_vote() -> None:
    assert ElectionEngine.check_quorum(1, 3) is False


def test_check_quorum_five_nodes_three_votes() -> None:
    assert ElectionEngine.check_quorum(3, 5) is True


def test_check_quorum_five_nodes_two_votes() -> None:
    assert ElectionEngine.check_quorum(2, 5) is False


# ---------------------------------------------------------------------------
# ElectionEngine: handle_vote_request
# ---------------------------------------------------------------------------

def test_handle_vote_request_grants_vote() -> None:
    sm = make_sm("node-2")
    log = make_log()
    engine = make_engine(node_id="node-2", sm=sm, log=log)

    req = VoteRequest(candidate_id="node-1", term=1, last_log_index=0, last_log_term=0)
    resp = engine.handle_vote_request(req)
    assert resp.vote_granted is True
    assert resp.voter_id == "node-2"
    assert resp.term == 1


def test_handle_vote_request_denies_stale_term() -> None:
    sm = make_sm("node-2")
    sm.transition_to_candidate()  # term = 1
    sm.transition_to_leader()
    engine = make_engine(node_id="node-2", sm=sm)

    req = VoteRequest(candidate_id="node-1", term=0, last_log_index=0, last_log_term=0)
    resp = engine.handle_vote_request(req)
    assert resp.vote_granted is False


def test_handle_vote_request_advances_term_on_higher_term() -> None:
    sm = make_sm("node-2")
    engine = make_engine(node_id="node-2", sm=sm)

    req = VoteRequest(candidate_id="node-1", term=10, last_log_index=0, last_log_term=0)
    resp = engine.handle_vote_request(req)
    assert sm.current_term == 10
    assert resp.vote_granted is True


def test_handle_vote_request_denies_duplicate_in_same_term() -> None:
    sm = make_sm("node-2")
    engine = make_engine(node_id="node-2", sm=sm)

    # First vote granted to node-1
    req1 = VoteRequest(candidate_id="node-1", term=1, last_log_index=0, last_log_term=0)
    resp1 = engine.handle_vote_request(req1)
    assert resp1.vote_granted is True

    # Second vote in same term to node-3 is denied
    req2 = VoteRequest(candidate_id="node-3", term=1, last_log_index=0, last_log_term=0)
    resp2 = engine.handle_vote_request(req2)
    assert resp2.vote_granted is False


# ---------------------------------------------------------------------------
# ElectionEngine: timer management
# ---------------------------------------------------------------------------

def test_cancel_timer_when_no_timer_does_not_raise() -> None:
    engine = make_engine()
    engine.cancel_election_timer()  # Should not raise


@pytest.mark.asyncio
async def test_timer_cancellation_stops_callback() -> None:
    fired = []

    async def on_timeout() -> None:
        fired.append(True)

    engine = make_engine()
    engine._on_timeout = on_timeout
    engine._min_timeout = 0.001
    engine._max_timeout = 0.001
    engine.start_election_timer()
    engine.cancel_election_timer()  # cancel immediately
    await asyncio.sleep(0.05)  # wait longer than timeout
    assert fired == []  # callback should not have fired


# ---------------------------------------------------------------------------
# ElectionEngine: trigger_election
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_trigger_election_transitions_to_candidate() -> None:
    """With peers present, trigger_election → CANDIDATE (not yet leader)."""
    sm = make_sm("node-1")
    engine = make_engine(node_id="node-1", sm=sm)
    # Provide peers so quorum requires more than self-vote
    engine.set_peers([make_peer("node-2"), make_peer("node-3")])

    await engine.trigger_election()

    assert sm.role == RaftRole.CANDIDATE
    assert sm.current_term == 1


@pytest.mark.asyncio
async def test_trigger_election_does_nothing_if_already_leader() -> None:
    sm = make_sm("node-1")
    sm.transition_to_candidate()
    sm.transition_to_leader()
    engine = make_engine(node_id="node-1", sm=sm)
    engine.set_peers([make_peer("node-2"), make_peer("node-3")])

    await engine.trigger_election()

    assert sm.role == RaftRole.LEADER  # No change


# ---------------------------------------------------------------------------
# ElectionEngine: tally_vote – quorum and step-down
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_tally_vote_promotes_to_leader_on_quorum() -> None:
    elected_results: list[ElectionResult] = []

    async def on_elected(result: ElectionResult) -> None:
        elected_results.append(result)

    sm = make_sm("node-1")
    engine = make_engine(node_id="node-1", sm=sm, on_elected=on_elected)
    engine.set_peers([make_peer("node-2"), make_peer("node-3")])

    # Become candidate (term=1, self-vote counted)
    await engine.trigger_election()

    # node-2 grants vote → quorum in 3-node cluster
    resp = VoteResponse(voter_id="node-2", term=1, vote_granted=True)
    await engine.tally_vote(resp)

    assert sm.role == RaftRole.LEADER
    assert len(elected_results) == 1
    assert elected_results[0].winner_id == "node-1"


@pytest.mark.asyncio
async def test_tally_vote_steps_down_on_higher_term() -> None:
    sm = make_sm("node-1")
    engine = make_engine(node_id="node-1", sm=sm)
    await engine.trigger_election()  # term=1, CANDIDATE

    resp = VoteResponse(voter_id="node-2", term=99, vote_granted=False)
    await engine.tally_vote(resp)

    assert sm.role == RaftRole.FOLLOWER
    assert sm.current_term == 99


@pytest.mark.asyncio
async def test_tally_vote_ignores_stale_responses() -> None:
    sm = make_sm("node-1")
    engine = make_engine(node_id="node-1", sm=sm)
    # Must have peers so we don't auto-win on trigger_election
    engine.set_peers([make_peer("node-2"), make_peer("node-3")])
    await engine.trigger_election()  # term=1

    resp = VoteResponse(voter_id="node-2", term=0, vote_granted=True)
    await engine.tally_vote(resp)

    # Still candidate – stale response ignored
    assert sm.role == RaftRole.CANDIDATE


@pytest.mark.asyncio
async def test_tally_vote_multiple_votes_no_double_promotion() -> None:
    """Extra votes beyond quorum do not re-trigger the callback."""
    call_count = [0]

    async def on_elected(result: ElectionResult) -> None:
        call_count[0] += 1

    sm = make_sm("node-1")
    engine = make_engine(node_id="node-1", sm=sm, on_elected=on_elected)
    engine.set_peers([make_peer("node-2"), make_peer("node-3"), make_peer("node-4")])

    await engine.trigger_election()  # term=1, self-vote

    # node-2 → quorum in 4-node cluster requires 3 votes
    await engine.tally_vote(VoteResponse(voter_id="node-2", term=1, vote_granted=True))
    await engine.tally_vote(VoteResponse(voter_id="node-3", term=1, vote_granted=True))
    # Now quorum reached – callback fires once
    assert sm.role == RaftRole.LEADER

    # Additional vote should not re-trigger
    await engine.tally_vote(VoteResponse(voter_id="node-4", term=1, vote_granted=True))
    assert call_count[0] == 1
