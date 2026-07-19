"""ElectionEngine – Raft leader election logic.

This module implements the leader election sub-protocol described in Raft §5.2
and §5.4.  It manages:

* Randomised election timers (``asyncio`` task-based, mockable in tests).
* Broadcasting VoteRequest RPCs to all cluster peers via the ``MessageBus``.
* Accumulating VoteResponse acknowledgements and detecting quorum.
* Handling VoteRequest messages received as a potential voter.
* Term advancement and automatic demotion on receiving a higher term.

The ``ElectionEngine`` is intentionally decoupled from the transport layer:
it serialises VoteRequest/VoteResponse models to plain dicts and dispatches
them through the ``MessageBus``.  It interacts with the ``RaftStateMachine``
for all state mutations and with the ``ConsensusLog`` to read log metadata
required for log-completeness checks.
"""

from __future__ import annotations

import asyncio
import random
from typing import Any, Callable, Coroutine, Dict, List, Optional

import structlog

from flock.consensus.exceptions import (
    InvalidTermError,
    QuorumNotReachedError,
)
from flock.consensus.log import ConsensusLog
from flock.consensus.models import (
    ElectionResult,
    RaftRole,
    VoteRequest,
    VoteResponse,
)
from flock.consensus.state_machine import RaftStateMachine
from flock.messaging.bus import MessageBus
from flock.messaging.models import MessageMetadata
from flock.protocol.packet import MessageType
from flock.types import NodeInfo

logger = structlog.get_logger()

# Callback type invoked when a new leader is elected
LeaderElectedCallback = Callable[[ElectionResult], Coroutine[Any, Any, None]]


class ElectionEngine:
    """Manages randomised election timers and vote solicitation.

    Args:
        node_id:           Stable identifier for this node.
        state_machine:     Shared Raft state machine (mutated on transitions).
        consensus_log:     Read-only access to local log metadata.
        message_bus:       Transport-independent message dispatcher.
        min_timeout_sec:   Lower bound for the randomised election timeout.
        max_timeout_sec:   Upper bound for the randomised election timeout.
        on_leader_elected: Async callback invoked when this node wins.
        on_timeout:        Async callback invoked when the timer fires.
    """

    def __init__(
        self,
        node_id: str,
        state_machine: RaftStateMachine,
        consensus_log: ConsensusLog,
        message_bus: MessageBus,
        min_timeout_sec: float = 0.15,
        max_timeout_sec: float = 0.30,
        on_leader_elected: Optional[LeaderElectedCallback] = None,
        on_timeout: Optional[Callable[[], Coroutine[Any, Any, None]]] = None,
    ) -> None:
        self.node_id = node_id
        self._sm = state_machine
        self._log = consensus_log
        self._bus = message_bus
        self._min_timeout = min_timeout_sec
        self._max_timeout = max_timeout_sec
        self._on_leader_elected = on_leader_elected
        self._on_timeout = on_timeout

        self._timer_task: Optional[asyncio.Task[None]] = None
        self._cluster_peers: List[NodeInfo] = []

    # ------------------------------------------------------------------
    # Peer management
    # ------------------------------------------------------------------

    def set_peers(self, peers: List[NodeInfo]) -> None:
        """Update the list of cluster peers used for vote broadcasting.

        Args:
            peers: All peer ``NodeInfo`` records *excluding* this node.
        """
        self._cluster_peers = list(peers)

    # ------------------------------------------------------------------
    # Election timer
    # ------------------------------------------------------------------

    def _random_timeout(self) -> float:
        """Return a uniformly randomised timeout within configured bounds."""
        return random.uniform(self._min_timeout, self._max_timeout)

    def start_election_timer(self) -> None:
        """Cancel any running timer and start a fresh randomised election timer.

        When the timer fires the ``_on_timeout`` callback is invoked, which
        the ``ConsensusService`` wires to ``trigger_election``.  In tests,
        the clock and random number generator are mocked so timers fire
        deterministically.
        """
        self.cancel_election_timer()
        delay = self._random_timeout()
        self._timer_task = asyncio.create_task(
            self._election_timer_coro(delay), name=f"election-timer-{self.node_id}"
        )
        logger.debug(
            "Election timer started",
            node_id=self.node_id,
            delay_sec=round(delay, 4),
        )

    def cancel_election_timer(self) -> None:
        """Cancel the running election timer if one exists."""
        if self._timer_task and not self._timer_task.done():
            self._timer_task.cancel()
            self._timer_task = None

    async def _election_timer_coro(self, delay: float) -> None:
        """Async coroutine that waits ``delay`` seconds then fires the callback."""
        try:
            await asyncio.sleep(delay)
            logger.debug("Election timer fired", node_id=self.node_id)
            if self._on_timeout:
                await self._on_timeout()
        except asyncio.CancelledError:
            logger.debug("Election timer cancelled", node_id=self.node_id)

    # ------------------------------------------------------------------
    # Vote solicitation
    # ------------------------------------------------------------------

    async def request_votes(self, peers: Optional[List[NodeInfo]] = None) -> None:
        """Broadcast VoteRequest RPCs to all cluster peers.

        Constructs a ``VoteRequest`` from the current state machine state
        and dispatches it to every peer via the ``MessageBus``.  Responses
        are handled asynchronously via the registered message handler.

        Args:
            peers: Override peer list; defaults to ``_cluster_peers``.
        """
        target_peers = peers if peers is not None else self._cluster_peers
        if not target_peers:
            logger.debug("No peers to request votes from", node_id=self.node_id)
            # Single-node cluster — elect self immediately
            await self._maybe_win_election(len(target_peers) + 1)
            return

        state = self._sm.state
        vote_req = VoteRequest(
            candidate_id=self.node_id,
            term=state.current_term,
            last_log_index=self._log.last_index,
            last_log_term=self._log.last_term,
        )
        payload = vote_req.model_dump()
        metadata = MessageMetadata(
            request_id=vote_req.request_id,
            custom={"type": "vote_request"},
        )

        for peer in target_peers:
            try:
                await self._bus.send(peer, MessageType.RAFT_REQUEST_VOTE, payload, metadata)
                logger.debug(
                    "Sent VoteRequest",
                    from_node=self.node_id,
                    to_node=peer.node_id,
                    term=state.current_term,
                )
            except Exception as exc:
                logger.warning(
                    "Failed to send VoteRequest",
                    to_node=peer.node_id,
                    error=str(exc),
                )

    # ------------------------------------------------------------------
    # Vote tallying
    # ------------------------------------------------------------------

    async def tally_vote(self, response: VoteResponse) -> None:
        """Process an incoming VoteResponse and promote to leader on quorum.

        If the response carries a higher term, this node steps down.

        Args:
            response: Parsed ``VoteResponse`` from a remote voter.
        """
        current_term = self._sm.current_term

        # Step down if we see a higher term
        if response.term > current_term:
            stepped = self._sm.update_term(response.term)
            if stepped:
                logger.info(
                    "Stepped down after receiving higher term in VoteResponse",
                    node_id=self.node_id,
                    new_term=response.term,
                )
            return

        # Ignore stale responses
        if response.term < current_term:
            logger.debug(
                "Ignoring stale VoteResponse",
                voter=response.voter_id,
                response_term=response.term,
                current_term=current_term,
            )
            return

        # Only count votes while still a candidate
        if self._sm.role != RaftRole.CANDIDATE:
            return

        if response.vote_granted:
            total_votes = self._sm.record_vote(response.voter_id)
            cluster_size = len(self._cluster_peers) + 1  # +1 for self
            logger.debug(
                "Vote granted",
                voter=response.voter_id,
                total_votes=total_votes,
                cluster_size=cluster_size,
            )
            await self._maybe_win_election(cluster_size)
        else:
            logger.debug(
                "Vote denied",
                voter=response.voter_id,
                reason=response.reason,
            )

    async def _maybe_win_election(self, cluster_size: int) -> None:
        """Check for quorum and promote to LEADER if achieved."""
        if self._sm.role != RaftRole.CANDIDATE:
            return
        votes = self._sm.vote_count()
        if self.check_quorum(votes, cluster_size):
            term = self._sm.current_term
            self._sm.transition_to_leader()
            self.cancel_election_timer()
            result = ElectionResult(
                term=term,
                winner_id=self.node_id,
                votes_received=votes,
                quorum_size=self._quorum_size(cluster_size),
            )
            logger.info(
                "Won leader election",
                node_id=self.node_id,
                term=term,
                votes=votes,
                quorum=self._quorum_size(cluster_size),
            )
            if self._on_leader_elected:
                await self._on_leader_elected(result)

    # ------------------------------------------------------------------
    # Incoming VoteRequest handling
    # ------------------------------------------------------------------

    def handle_vote_request(self, request: VoteRequest) -> VoteResponse:
        """Evaluate an incoming VoteRequest and return a VoteResponse.

        Applies Raft §5.2 (one vote per term) and §5.4.1 (log completeness).
        If the request carries a higher term, this node steps down first.

        Args:
            request: Parsed ``VoteRequest`` from a remote candidate.

        Returns:
            ``VoteResponse`` with ``vote_granted`` set appropriately.
        """
        # Step down if we observe a higher term
        if request.term > self._sm.current_term:
            self._sm.update_term(request.term)

        grant, reason = self._sm.can_vote_for(
            candidate_id=request.candidate_id,
            candidate_term=request.term,
            candidate_last_log_index=request.last_log_index,
            candidate_last_log_term=request.last_log_term,
            local_last_log_index=self._log.last_index,
            local_last_log_term=self._log.last_term,
        )

        if grant:
            # Record our vote by transitioning to follower with voted_for set
            self._sm.transition_to_follower(
                term=request.term,
                voted_for=request.candidate_id,
            )
            logger.info(
                "Granted vote",
                voter=self.node_id,
                candidate=request.candidate_id,
                term=request.term,
            )
        else:
            logger.debug(
                "Denied vote",
                voter=self.node_id,
                candidate=request.candidate_id,
                reason=reason,
            )

        return VoteResponse(
            voter_id=self.node_id,
            term=self._sm.current_term,
            vote_granted=grant,
            reason=reason,
            correlation_id=request.request_id,
        )

    # ------------------------------------------------------------------
    # Quorum helpers
    # ------------------------------------------------------------------

    @staticmethod
    def check_quorum(votes: int, cluster_size: int) -> bool:
        """Return ``True`` if ``votes`` constitutes a majority.

        Raft requires a strict majority: ``votes > cluster_size / 2``.

        Args:
            votes:        Number of affirmative votes (including self).
            cluster_size: Total number of nodes in the cluster.
        """
        return votes > cluster_size // 2

    @staticmethod
    def _quorum_size(cluster_size: int) -> int:
        """Minimum votes needed for a majority."""
        return cluster_size // 2 + 1

    # ------------------------------------------------------------------
    # Election trigger (called by ConsensusService on timer fire)
    # ------------------------------------------------------------------

    async def trigger_election(self) -> None:
        """Start a new election: advance term, transition to candidate, broadcast.

        This is the canonical entry point invoked when the election timer
        fires.  The ``ConsensusService`` calls this method via the
        ``on_timeout`` callback.
        """
        # Do not start an election if already leader
        if self._sm.role == RaftRole.LEADER:
            return

        logger.info("Election triggered", node_id=self.node_id)
        new_term = self._sm.transition_to_candidate()
        logger.info(
            "Became CANDIDATE",
            node_id=self.node_id,
            term=new_term,
        )
        await self.request_votes()
        # Restart the timer in case we don't win (split vote → retry)
        self.start_election_timer()
