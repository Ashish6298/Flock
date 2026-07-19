"""RaftStateMachine – deterministic role finite-state machine for Raft.

The ``RaftStateMachine`` is the single authoritative source of mutable Raft
state on a node.  It owns the current ``RaftNodeState`` and exposes explicit
transition methods that enforce Raft's safety rules:

* A node may only vote once per term.
* Terms only increase, never decrease.
* A leader may only be demoted by receiving a higher term.
* Commit index never decreases.

All state mutations are performed under a threading lock so that the
``ElectionEngine`` and ``ReplicationEngine`` can safely call transition
methods from different asyncio tasks (which may run on different threads in a
``ThreadPoolExecutor``-backed event loop).

Usage example::

    sm = RaftStateMachine(node_id="node-1")
    sm.transition_to_candidate()     # term 0 → 1, role FOLLOWER → CANDIDATE
    sm.transition_to_leader()        # role CANDIDATE → LEADER
    sm.update_term(5)                # any higher term → FOLLOWER, term = 5
"""

from __future__ import annotations

import threading
from typing import Optional, Set

import structlog

from flock.consensus.exceptions import (
    ConsensusViolationError,
    InvalidTermError,
)
from flock.consensus.models import RaftNodeState, RaftRole

logger = structlog.get_logger()


class RaftStateMachine:
    """Owns and guards the authoritative Raft state for a single node.

    All public methods are thread-safe.  Callers must use the transition
    methods rather than mutating state directly.

    Attributes:
        node_id:  Stable identifier for this node (immutable).
    """

    def __init__(self, node_id: str) -> None:
        self._state = RaftNodeState(node_id=node_id)
        self._votes_received: Set[str] = set()   # node_ids that voted FOR us
        self._lock = threading.Lock()

    # ------------------------------------------------------------------
    # Read-only access
    # ------------------------------------------------------------------

    @property
    def state(self) -> RaftNodeState:
        """Return a snapshot of the current Raft state (immutable copy)."""
        with self._lock:
            return self._state

    @property
    def current_term(self) -> int:
        """Convenience accessor for the current election term."""
        with self._lock:
            return self._state.current_term

    @property
    def role(self) -> RaftRole:
        """Convenience accessor for the current Raft role."""
        with self._lock:
            return self._state.role

    @property
    def leader_id(self) -> Optional[str]:
        """Convenience accessor for the known leader ID."""
        with self._lock:
            return self._state.leader_id

    @property
    def voted_for(self) -> Optional[str]:
        """Convenience accessor for voted_for in the current term."""
        with self._lock:
            return self._state.voted_for

    @property
    def commit_index(self) -> int:
        """Convenience accessor for the commit index."""
        with self._lock:
            return self._state.commit_index

    # ------------------------------------------------------------------
    # Role transitions
    # ------------------------------------------------------------------

    def transition_to_follower(
        self, term: int, leader_id: Optional[str] = None, voted_for: Optional[str] = None
    ) -> None:
        """Demote this node to FOLLOWER for ``term``.

        If ``term`` is greater than ``current_term``, the node updates its
        term and clears ``voted_for`` (a new term means a fresh vote slate).

        Args:
            term:       The term to enter as follower.
            leader_id:  The node_id of the known leader (may be ``None``).
            voted_for:  Optionally preserve or set a ``voted_for`` value
                        (used when receiving a VoteResponse).

        Raises:
            InvalidTermError: If ``term`` is less than current term.
        """
        with self._lock:
            current = self._state.current_term
            if term < current:
                raise InvalidTermError(
                    f"Cannot transition to follower: incoming term {term} "
                    f"< current term {current}"
                )
            new_term = max(term, current)
            # When the term advances, the vote slate resets
            new_voted_for = voted_for if term == current else voted_for
            if term > current:
                new_voted_for = None  # fresh slate for new term
            self._votes_received.clear()
            self._state = self._state.with_updates(
                role=RaftRole.FOLLOWER,
                current_term=new_term,
                voted_for=new_voted_for,
                leader_id=leader_id,
            )
            logger.debug(
                "Transitioned to FOLLOWER",
                node_id=self._state.node_id,
                term=new_term,
                leader_id=leader_id,
            )

    def transition_to_candidate(self) -> int:
        """Advance this node to CANDIDATE, incrementing the term.

        This node automatically votes for itself.

        Returns:
            The new (incremented) election term.

        Raises:
            ConsensusViolationError: If already a leader (leaders do not
                spontaneously start elections).
        """
        with self._lock:
            if self._state.role == RaftRole.LEADER:
                raise ConsensusViolationError(
                    "A LEADER cannot transition directly to CANDIDATE"
                )
            new_term = self._state.current_term + 1
            node_id = self._state.node_id
            self._votes_received = {node_id}  # self-vote
            self._state = self._state.with_updates(
                role=RaftRole.CANDIDATE,
                current_term=new_term,
                voted_for=node_id,
                leader_id=None,
            )
            logger.info(
                "Transitioned to CANDIDATE",
                node_id=node_id,
                term=new_term,
            )
            return new_term

    def transition_to_leader(self) -> None:
        """Promote this CANDIDATE to LEADER.

        Only valid when this node is currently a CANDIDATE.  After promotion
        the node declares itself the known leader for the current term.

        Raises:
            ConsensusViolationError: If not currently CANDIDATE.
        """
        with self._lock:
            if self._state.role != RaftRole.CANDIDATE:
                raise ConsensusViolationError(
                    f"Only a CANDIDATE can become LEADER; current role is "
                    f"{self._state.role}"
                )
            node_id = self._state.node_id
            self._state = self._state.with_updates(
                role=RaftRole.LEADER,
                leader_id=node_id,
            )
            logger.info(
                "Transitioned to LEADER",
                node_id=node_id,
                term=self._state.current_term,
            )

    # ------------------------------------------------------------------
    # Term management
    # ------------------------------------------------------------------

    def update_term(self, new_term: int) -> bool:
        """Advance to ``new_term`` and step down to FOLLOWER if necessary.

        This is called whenever a higher term is observed in an incoming RPC.
        If ``new_term`` is greater than ``current_term``, the node always
        reverts to FOLLOWER and clears ``voted_for``.

        Args:
            new_term: Observed term from a remote RPC.

        Returns:
            ``True`` if the term was updated (and a step-down occurred),
            ``False`` if ``new_term <= current_term``.
        """
        with self._lock:
            if new_term <= self._state.current_term:
                return False
            self._votes_received.clear()
            self._state = self._state.with_updates(
                current_term=new_term,
                role=RaftRole.FOLLOWER,
                voted_for=None,
                leader_id=None,
            )
            logger.info(
                "Term updated – stepped down to FOLLOWER",
                node_id=self._state.node_id,
                new_term=new_term,
            )
            return True

    # ------------------------------------------------------------------
    # Vote accounting
    # ------------------------------------------------------------------

    def can_vote_for(
        self,
        candidate_id: str,
        candidate_term: int,
        candidate_last_log_index: int,
        candidate_last_log_term: int,
        local_last_log_index: int,
        local_last_log_term: int,
    ) -> tuple[bool, str]:
        """Determine whether this node may grant a vote to the candidate.

        Implements Raft §5.2 (one vote per term) and §5.4.1 (log
        completeness — the candidate's log must be at least as up-to-date).

        Args:
            candidate_id:             Node ID of the requesting candidate.
            candidate_term:           Term carried in the VoteRequest.
            candidate_last_log_index: Candidate's last log index.
            candidate_last_log_term:  Term of candidate's last log entry.
            local_last_log_index:     This node's last log index.
            local_last_log_term:      Term of this node's last log entry.

        Returns:
            Tuple of (grant: bool, reason: str).
        """
        with self._lock:
            # Term check — reject stale candidates
            if candidate_term < self._state.current_term:
                return False, (
                    f"Stale term: candidate term {candidate_term} < "
                    f"current term {self._state.current_term}"
                )

            # One-vote-per-term rule
            voted_for = self._state.voted_for
            if voted_for is not None and voted_for != candidate_id:
                return False, (
                    f"Already voted for {voted_for} in term "
                    f"{self._state.current_term}"
                )

            # Log completeness (§5.4.1)
            # Candidate's log is at least as up-to-date if:
            #   its last term is greater, OR
            #   last terms are equal and its log is at least as long.
            log_ok = (
                candidate_last_log_term > local_last_log_term
                or (
                    candidate_last_log_term == local_last_log_term
                    and candidate_last_log_index >= local_last_log_index
                )
            )
            if not log_ok:
                return False, (
                    f"Candidate log stale: candidate ({candidate_last_log_index},"
                    f"{candidate_last_log_term}) vs local ({local_last_log_index},"
                    f"{local_last_log_term})"
                )

            return True, "granted"

    def record_vote(self, voter_id: str) -> int:
        """Record a vote granted by ``voter_id`` for the current candidacy.

        Args:
            voter_id: Node ID that granted the vote.

        Returns:
            Total number of votes received so far (including self-vote).
        """
        with self._lock:
            self._votes_received.add(voter_id)
            return len(self._votes_received)

    def vote_count(self) -> int:
        """Return the number of votes received in the current candidacy."""
        with self._lock:
            return len(self._votes_received)

    # ------------------------------------------------------------------
    # Commit index advancement
    # ------------------------------------------------------------------

    def advance_commit_index(self, index: int) -> bool:
        """Advance the commit index to ``index`` if it is higher.

        Args:
            index: New candidate commit index.

        Returns:
            ``True`` if the commit index was advanced.
        """
        with self._lock:
            if index > self._state.commit_index:
                self._state = self._state.with_updates(commit_index=index)
                return True
            return False

    # ------------------------------------------------------------------
    # Leader tracking
    # ------------------------------------------------------------------

    def set_leader(self, leader_id: str) -> None:
        """Record the current known leader without changing role or term."""
        with self._lock:
            self._state = self._state.with_updates(leader_id=leader_id)
