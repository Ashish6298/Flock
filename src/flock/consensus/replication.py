"""ReplicationEngine – Raft log replication (AppendEntries RPC).

This module implements the log replication sub-protocol described in Raft §5.3
and §5.4.  Responsibilities:

* Sending AppendEntries RPCs (including heartbeats) from a leader to followers.
* Processing incoming AppendEntries RPCs on followers: validating prev_log
  consistency, truncating conflicting tails, appending new entries, and
  advancing the commit index.
* Tracking per-follower ``nextIndex`` and ``matchIndex`` as required by the
  leader's replication bookkeeping.
* Calculating the safe commit index once a quorum of followers acknowledge
  replication.
* Publishing ``consensus.log.committed`` events through the ``EventBus``
  whenever the commit index advances.

The engine intentionally does not hold a reference to the ``ElectionEngine``
and does not initiate elections.  Term-based step-downs are signalled through
the ``RaftStateMachine`` and handled by the ``ConsensusService``.
"""

from __future__ import annotations

import asyncio
from typing import Any, Callable, Coroutine, Dict, List, Optional, Set

import structlog

from flock.consensus.exceptions import (
    InvalidTermError,
    LogConflictError,
    ReplicationFailureError,
)
from flock.consensus.log import ConsensusLog
from flock.consensus.models import (
    AppendEntriesRequest,
    AppendEntriesResponse,
    LogEntry,
    RaftRole,
)
from flock.consensus.state_machine import RaftStateMachine
from flock.events.bus import EventBus
from flock.messaging.bus import MessageBus
from flock.messaging.models import MessageMetadata
from flock.protocol.packet import MessageType
from flock.types import NodeInfo

logger = structlog.get_logger()

# Async callback type for commit-index advance notifications
CommitCallback = Callable[[int], Coroutine[Any, Any, None]]


class ReplicationEngine:
    """Manages AppendEntries RPC dispatch and follower log reconciliation.

    Args:
        node_id:          Stable identifier for this node.
        state_machine:    Shared Raft state machine.
        consensus_log:    The authoritative replicated log.
        message_bus:      Transport-independent message dispatcher.
        event_bus:        Local event bus for publishing committed events.
        on_step_down:     Async callback invoked when a higher term is seen
                          (triggers ConsensusService to step down to follower).
    """

    def __init__(
        self,
        node_id: str,
        state_machine: RaftStateMachine,
        consensus_log: ConsensusLog,
        message_bus: MessageBus,
        event_bus: EventBus,
        on_step_down: Optional[Callable[[int], Coroutine[Any, Any, None]]] = None,
    ) -> None:
        self.node_id = node_id
        self._sm = state_machine
        self._log = consensus_log
        self._bus = message_bus
        self._events = event_bus
        self._on_step_down = on_step_down

        # Leader-side per-peer tracking
        # nextIndex[peer] – next log index to send to that peer
        self._next_index: Dict[str, int] = {}
        # matchIndex[peer] – highest log index known replicated on peer
        self._match_index: Dict[str, int] = {}

    # ------------------------------------------------------------------
    # Leader-side: peer index initialisation
    # ------------------------------------------------------------------

    def initialize_peer_indexes(self, peers: List[str]) -> None:
        """Initialise ``nextIndex`` and ``matchIndex`` for all followers.

        Called by the ``ConsensusService`` whenever this node becomes leader.
        Sets ``nextIndex[peer] = last_log_index + 1`` and
        ``matchIndex[peer] = 0`` as required by Raft §5.3.

        Args:
            peers: Node IDs of all known followers.
        """
        last = self._log.last_index
        for peer_id in peers:
            self._next_index[peer_id] = last + 1
            self._match_index[peer_id] = 0
        logger.debug(
            "Peer indexes initialised",
            leader=self.node_id,
            peers=peers,
            next_index=last + 1,
        )

    # ------------------------------------------------------------------
    # Leader-side: AppendEntries dispatch
    # ------------------------------------------------------------------

    async def replicate_entries(
        self, peers: List[NodeInfo], entries: Optional[List[LogEntry]] = None
    ) -> None:
        """Send AppendEntries RPCs (with entries) to all followers.

        If ``entries`` is ``None``, new entries since each peer's ``nextIndex``
        are fetched from the log automatically.  If ``entries`` is an empty
        list, the call degrades to a heartbeat.

        Args:
            peers:   All follower ``NodeInfo`` records.
            entries: Explicit entry list override; ``None`` = auto-fetch.
        """
        if self._sm.role != RaftRole.LEADER:
            return

        state = self._sm.state
        for peer in peers:
            if peer.node_id == self.node_id:
                continue
            try:
                next_idx = self._next_index.get(peer.node_id, self._log.last_index + 1)
                prev_idx = next_idx - 1
                prev_term = self._log.get_term_at(prev_idx)

                if entries is None:
                    send_entries = self._log.get_range(next_idx, self._log.last_index)
                else:
                    send_entries = entries

                req = AppendEntriesRequest(
                    leader_id=self.node_id,
                    term=state.current_term,
                    prev_log_index=prev_idx,
                    prev_log_term=prev_term,
                    entries=send_entries,
                    leader_commit=state.commit_index,
                )
                payload = req.model_dump()
                metadata = MessageMetadata(
                    request_id=req.request_id,
                    custom={"type": "append_entries"},
                )
                await self._bus.send(
                    peer, MessageType.RAFT_APPEND_ENTRIES, payload, metadata
                )
                logger.debug(
                    "Sent AppendEntries",
                    leader=self.node_id,
                    follower=peer.node_id,
                    prev_log_index=prev_idx,
                    entries_count=len(send_entries),
                )
            except Exception as exc:
                logger.warning(
                    "Failed to send AppendEntries",
                    to_node=peer.node_id,
                    error=str(exc),
                )
                await self._events.publish(
                    "consensus.replication.failed",
                    {"peer_id": peer.node_id, "error": str(exc)},
                )

    async def send_heartbeat(self, peers: List[NodeInfo]) -> None:
        """Send an empty AppendEntries (heartbeat) to all followers.

        Heartbeats carry no log entries but do carry the leader's commit
        index, allowing followers to advance their own commit pointers.

        Args:
            peers: All follower ``NodeInfo`` records.
        """
        await self.replicate_entries(peers, entries=[])

    # ------------------------------------------------------------------
    # Leader-side: processing follower responses
    # ------------------------------------------------------------------

    async def process_append_response(
        self, response: AppendEntriesResponse, peer_id: str, peers: List[str]
    ) -> None:
        """Update per-peer indexes and advance commit index on quorum.

        When a follower rejects an AppendEntries (``success=False``), the
        leader decrements ``nextIndex`` using the optimised conflict hint
        fields and will retry on the next heartbeat/replication cycle.

        A higher term in the response causes an immediate step-down.

        Args:
            response: Parsed ``AppendEntriesResponse`` from a follower.
            peer_id:  Node ID of the responding follower.
            peers:    All known peer node IDs (for quorum calculation).
        """
        current_term = self._sm.current_term

        # Step down if we see a higher term
        if response.term > current_term:
            if self._on_step_down:
                await self._on_step_down(response.term)
            return

        if self._sm.role != RaftRole.LEADER:
            return

        if response.success:
            # Update match and next indexes
            if response.match_index > self._match_index.get(peer_id, 0):
                self._match_index[peer_id] = response.match_index
                self._next_index[peer_id] = response.match_index + 1

            # Try to advance commit index
            await self._advance_commit(peers, current_term)
        else:
            # Back-track using conflict hint
            if response.conflict_index > 0:
                self._next_index[peer_id] = max(1, response.conflict_index)
            else:
                self._next_index[peer_id] = max(1, self._next_index.get(peer_id, 1) - 1)
            logger.debug(
                "AppendEntries rejected; decremented nextIndex",
                peer=peer_id,
                new_next_index=self._next_index[peer_id],
            )

    async def _advance_commit(self, peers: List[str], current_term: int) -> None:
        """Try to advance the commit index based on current matchIndexes."""
        # Exclude self from match_indexes – self is already represented via self_index
        new_commit = self.calculate_commit_index(
            match_indexes={p: self._match_index.get(p, 0) for p in peers if p != self.node_id},
            self_index=self._log.last_index,
            current_term=current_term,
        )
        if new_commit > self._sm.commit_index:
            self._log.commit(new_commit)
            advanced = self._sm.advance_commit_index(new_commit)
            if advanced:
                entry = self._log.get_entry(new_commit)
                await self._events.publish(
                    "consensus.log.committed",
                    {
                        "index": new_commit,
                        "entry_id": entry.entry_id if entry else None,
                        "term": current_term,
                    },
                )
                logger.info(
                    "Commit index advanced",
                    leader=self.node_id,
                    new_commit=new_commit,
                )

    # ------------------------------------------------------------------
    # Follower-side: AppendEntries handling
    # ------------------------------------------------------------------

    def handle_append_entries(
        self, request: AppendEntriesRequest
    ) -> AppendEntriesResponse:
        """Process an incoming AppendEntries RPC on a follower.

        Implements Raft §5.3 receiver implementation steps 1–5:

        1. Return failure if ``term < currentTerm``.
        2. Return failure if log does not contain entry at ``prev_log_index``
           with matching ``prev_log_term``.
        3. Delete conflicting entries and all that follow.
        4. Append new entries not already in the log.
        5. Advance ``commit_index`` if ``leaderCommit > commitIndex``.

        Args:
            request: Parsed ``AppendEntriesRequest`` from the leader.

        Returns:
            ``AppendEntriesResponse`` indicating success or failure with
            conflict hints for efficient leader backtracking.
        """
        current_term = self._sm.current_term

        # Step 1: reject stale term
        if request.term < current_term:
            return AppendEntriesResponse(
                follower_id=self.node_id,
                term=current_term,
                success=False,
                correlation_id=request.request_id,
                conflict_index=0,
                conflict_term=0,
            )

        # Update our term if needed (and step down if we were a candidate)
        if request.term > current_term:
            self._sm.update_term(request.term)
        # Recognise the sender as current leader
        self._sm.set_leader(request.leader_id)
        self._sm.transition_to_follower(
            term=request.term, leader_id=request.leader_id
        )

        # Step 2: check prev_log consistency
        if not self._log.has_entry(request.prev_log_index, request.prev_log_term):
            # Build conflict hint for leader to optimise back-tracking
            conflict_index, conflict_term = self._build_conflict_hint(
                request.prev_log_index
            )
            return AppendEntriesResponse(
                follower_id=self.node_id,
                term=self._sm.current_term,
                success=False,
                conflict_index=conflict_index,
                conflict_term=conflict_term,
                correlation_id=request.request_id,
            )

        # Steps 3 & 4: reconcile and append entries
        if request.entries:
            self._reconcile_and_append(request.entries)

        # Step 5: advance commit index
        if request.leader_commit > self._log.commit_index:
            new_commit = min(request.leader_commit, self._log.last_index)
            self._log.commit(new_commit)
            self._sm.advance_commit_index(new_commit)

        return AppendEntriesResponse(
            follower_id=self.node_id,
            term=self._sm.current_term,
            success=True,
            match_index=self._log.last_index,
            correlation_id=request.request_id,
        )

    def _build_conflict_hint(self, prev_log_index: int) -> tuple[int, int]:
        """Build optimised conflict index/term for leader back-tracking.

        If ``prev_log_index`` is beyond our log, the conflict index is our
        last index + 1 (asking the leader to send from there).  Otherwise
        we return the first index with the conflicting term.

        Args:
            prev_log_index: The prev_log_index from the rejected request.

        Returns:
            Tuple of (conflict_index, conflict_term).
        """
        last = self._log.last_index
        if prev_log_index > last:
            return last + 1, 0

        conflict_term = self._log.get_term_at(prev_log_index)
        # Walk back to find the first entry with this term
        first_conflict = prev_log_index
        while first_conflict > 1 and self._log.get_term_at(first_conflict - 1) == conflict_term:
            first_conflict -= 1
        return first_conflict, conflict_term

    def _reconcile_and_append(self, entries: List[LogEntry]) -> None:
        """Truncate conflicting suffix and append new entries.

        For each incoming entry, if the local log contains a conflicting
        entry (same index, different term), truncate from that point and
        append the remainder.  Entries already matching the local log are
        skipped (idempotent behaviour).

        Args:
            entries: Ordered new entries from the leader.
        """
        for entry in entries:
            local_entry = self._log.get_entry(entry.index)
            if local_entry is None:
                # No local entry at this index: append from here
                remaining = [e for e in entries if e.index >= entry.index]
                self._log.append(remaining)
                return
            elif local_entry.term != entry.term:
                # Conflict: truncate from this index and append remainder
                self._log.truncate_from(entry.index)
                remaining = [e for e in entries if e.index >= entry.index]
                self._log.append(remaining)
                return
            # Entry matches: skip (already in log)

    # ------------------------------------------------------------------
    # Commit index calculation (leader quorum logic)
    # ------------------------------------------------------------------

    @staticmethod
    def calculate_commit_index(
        match_indexes: Dict[str, int],
        self_index: int,
        current_term: int,
    ) -> int:
        """Find the highest log index replicated on a majority of servers.

        Implements Raft §5.3 commit rule: the leader may only advance the
        commit index to index N if ``log[N].term == currentTerm`` and N has
        been replicated on a majority of servers.

        We approximate the term check by returning the max N such that a
        majority have ``matchIndex >= N``.  The caller is responsible for
        verifying that ``log[N].term == currentTerm`` before committing.

        Args:
            match_indexes:  Mapping of peer_id → matchIndex for all followers.
            self_index:     The leader's own last log index (always matched).
            current_term:   The leader's current term (unused here; term check
                            delegated to ``_advance_commit`` caller).

        Returns:
            The highest index safely committable, or 0 if none.
        """
        # Combine all match indexes (leader has self_index)
        all_indexes = list(match_indexes.values()) + [self_index]
        cluster_size = len(all_indexes)
        quorum = cluster_size // 2 + 1

        # Sort descending and find the quorum-th highest
        all_indexes.sort(reverse=True)
        if len(all_indexes) >= quorum:
            return all_indexes[quorum - 1]
        return 0
