"""ConsensusService – top-level Raft consensus orchestrator.

This module ties together the ``RaftStateMachine``, ``ConsensusLog``,
``ElectionEngine``, and ``ReplicationEngine`` into a single high-level service
that is integrated with the rest of the Flock framework.  The service:

* Registers eight message handlers with the ``MessageBus`` router covering
  all Raft protocol message types defined in Phase 12.
* Starts and stops the election timer lifecycle.
* Broadcasts leader heartbeats on a configurable interval while this node
  is leader.
* Publishes structured events on the ``EventBus`` for all significant
  consensus state changes.
* Provides a ``submit_command`` API for application code to append entries
  to the replicated log (leader-only).

Integration points with existing Flock subsystems:
* **Cluster Membership**: ``MembershipRegistry`` is consulted to enumerate
  active peers for vote broadcasting and heartbeat targets.
* **Heartbeat**: ``HealthRegistry`` may be consulted to exclude unreachable
  nodes from replication targets (future optimisation; not required for
  correctness in Phase 12).
* **No reverse dependencies**: Scheduler, Placement, Recovery, and Runtime
  subsystems remain completely unaware of consensus internals.

Events published on the ``EventBus``:
    ``consensus.leader.elected``    – ``{leader_id: str, term: int}``
    ``consensus.term.changed``      – ``{old_term: int, new_term: int}``
    ``consensus.log.committed``     – ``{index: int, entry_id: str, term: int}``
    ``consensus.replication.failed``– ``{peer_id: str, error: str}``
"""

from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Optional

import structlog

from flock.cluster.models import ClusterMemberStatus
from flock.cluster.registry import MembershipRegistry
from flock.consensus.election import ElectionEngine
from flock.consensus.exceptions import LeaderUnavailableError
from flock.consensus.log import ConsensusLog
from flock.consensus.models import (
    AppendEntriesRequest,
    AppendEntriesResponse,
    HeartbeatPayload,
    LeaderAnnouncePayload,
    LogEntry,
    LogSyncRequest,
    LogSyncResponse,
    RaftRole,
    VoteRequest,
    VoteResponse,
    ElectionResult,
)
from flock.consensus.replication import ReplicationEngine
from flock.consensus.state_machine import RaftStateMachine
from flock.events.bus import EventBus
from flock.messaging.bus import MessageBus
from flock.messaging.handlers import MessageHandler
from flock.messaging.models import MessageContext, MessageMetadata
from flock.protocol.packet import MessageType
from flock.types import NodeInfo

logger = structlog.get_logger()


class ConsensusService:
    """High-level Raft consensus coordinator for a Flock node.

    Args:
        node_id:              Stable identifier for this node.
        message_bus:          Transport-independent message dispatcher.
        event_bus:            Local event bus for status notifications.
        membership_registry:  Provides active cluster members.
        min_election_timeout: Lower bound of randomised election timeout (s).
        max_election_timeout: Upper bound of randomised election timeout (s).
        heartbeat_interval:   Leader heartbeat broadcast interval (s).
    """

    def __init__(
        self,
        node_id: str,
        message_bus: MessageBus,
        event_bus: EventBus,
        membership_registry: MembershipRegistry,
        min_election_timeout: float = 0.15,
        max_election_timeout: float = 0.30,
        heartbeat_interval: float = 0.05,
    ) -> None:
        self.node_id = node_id
        self._bus = message_bus
        self._events = event_bus
        self._membership = membership_registry
        self._heartbeat_interval = heartbeat_interval

        # Core Raft components
        self._log = ConsensusLog()
        self._sm = RaftStateMachine(node_id=node_id)

        self._replication = ReplicationEngine(
            node_id=node_id,
            state_machine=self._sm,
            consensus_log=self._log,
            message_bus=message_bus,
            event_bus=event_bus,
            on_step_down=self._on_higher_term_observed,
        )

        self._election = ElectionEngine(
            node_id=node_id,
            state_machine=self._sm,
            consensus_log=self._log,
            message_bus=message_bus,
            min_timeout_sec=min_election_timeout,
            max_timeout_sec=max_election_timeout,
            on_leader_elected=self._on_leader_elected,
            on_timeout=self._election.trigger_election if False else None,
        )
        # Wire the timeout callback after construction to avoid forward ref
        self._election._on_timeout = self._on_election_timeout

        self._heartbeat_task: Optional[asyncio.Task[None]] = None
        self._running = False

        # Register all Raft message handlers
        self._register_handlers()

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def start(self) -> None:
        """Start the consensus service and begin participation in elections."""
        if self._running:
            return
        self._running = True
        self._election.start_election_timer()
        logger.info("ConsensusService started", node_id=self.node_id)

    async def stop(self) -> None:
        """Stop the consensus service, cancelling timers gracefully."""
        self._running = False
        self._election.cancel_election_timer()
        if self._heartbeat_task and not self._heartbeat_task.done():
            self._heartbeat_task.cancel()
            try:
                await self._heartbeat_task
            except asyncio.CancelledError:
                pass

        # Step down to follower on clean shutdown
        current_term = self._sm.current_term
        if self._sm.role != RaftRole.FOLLOWER:
            self._sm.transition_to_follower(term=current_term)

        logger.info("ConsensusService stopped", node_id=self.node_id)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def is_leader(self) -> bool:
        """Return ``True`` if this node is the current Raft leader."""
        return self._sm.role == RaftRole.LEADER

    def get_leader_id(self) -> Optional[str]:
        """Return the node_id of the known leader, or ``None``."""
        return self._sm.leader_id

    def get_current_term(self) -> int:
        """Return the current Raft election term."""
        return self._sm.current_term

    def get_commit_index(self) -> int:
        """Return the current committed log index."""
        return self._log.commit_index

    async def submit_command(self, command: bytes) -> LogEntry:
        """Append a command to the replicated log (leader-only).

        Creates a new ``LogEntry`` with the next sequential index and the
        current term, appends it to the local log, then triggers replication
        to all followers.

        Args:
            command: Opaque application-layer bytes payload.

        Returns:
            The newly created ``LogEntry``.

        Raises:
            LeaderUnavailableError: If this node is not currently the leader.
        """
        if not self.is_leader():
            leader = self.get_leader_id()
            raise LeaderUnavailableError(
                f"Cannot submit command: this node ({self.node_id}) is not the "
                f"leader. Known leader: {leader}"
            )

        next_index = self._log.last_index + 1
        entry = LogEntry(
            index=next_index,
            term=self._sm.current_term,
            command=command,
        )
        self._log.append([entry])
        logger.info(
            "Command submitted to log",
            leader=self.node_id,
            index=next_index,
            term=self._sm.current_term,
        )

        # Trigger replication to all followers
        peers = self._get_peer_node_infos()
        await self._replication.replicate_entries(peers)
        return entry

    # ------------------------------------------------------------------
    # Internal callbacks
    # ------------------------------------------------------------------

    async def _on_election_timeout(self) -> None:
        """Called when the election timer fires; triggers a new election."""
        await self._election.trigger_election()

    async def _on_leader_elected(self, result: ElectionResult) -> None:
        """Invoked by ElectionEngine when this node wins an election."""
        old_term = result.term - 1
        await self._events.publish(
            "consensus.leader.elected",
            {"leader_id": self.node_id, "term": result.term},
        )
        await self._events.publish(
            "consensus.term.changed",
            {"old_term": old_term, "new_term": result.term},
        )
        logger.info(
            "Leadership acquired",
            node_id=self.node_id,
            term=result.term,
            votes=result.votes_received,
        )

        # Initialise follower tracking indexes
        peer_ids = [
            m.node_id
            for m in self._membership.list_members(ClusterMemberStatus.ACTIVE)
            if m.node_id != self.node_id
        ]
        self._replication.initialize_peer_indexes(peer_ids)

        # Broadcast leader announcement
        await self._broadcast_leader_announce(result.term)

        # Start heartbeat loop
        self._heartbeat_task = asyncio.create_task(
            self._heartbeat_loop(), name=f"heartbeat-{self.node_id}"
        )

    async def _on_higher_term_observed(self, new_term: int) -> None:
        """Called when a higher term is seen in an AppendEntries response."""
        old_term = self._sm.current_term
        stepped = self._sm.update_term(new_term)
        if stepped:
            # Cancel heartbeat if we were leader
            if self._heartbeat_task and not self._heartbeat_task.done():
                self._heartbeat_task.cancel()
            # Restart election timer as a follower
            self._election.start_election_timer()
            await self._events.publish(
                "consensus.term.changed",
                {"old_term": old_term, "new_term": new_term},
            )

    # ------------------------------------------------------------------
    # Heartbeat loop (leader only)
    # ------------------------------------------------------------------

    async def _heartbeat_loop(self) -> None:
        """Periodically broadcast heartbeats to all followers while leader."""
        while self._running and self._sm.role == RaftRole.LEADER:
            try:
                peers = self._get_peer_node_infos()
                await self._replication.send_heartbeat(peers)
                logger.debug("Heartbeat sent", leader=self.node_id)
            except Exception as exc:
                logger.warning("Heartbeat loop error", error=str(exc))
            await asyncio.sleep(self._heartbeat_interval)

    # ------------------------------------------------------------------
    # Leader announcement broadcast
    # ------------------------------------------------------------------

    async def _broadcast_leader_announce(self, term: int) -> None:
        """Send a RAFT_LEADER_ANNOUNCE message to all peers."""
        payload = LeaderAnnouncePayload(
            leader_id=self.node_id, term=term
        ).model_dump()
        for peer in self._get_peer_node_infos():
            try:
                await self._bus.send(peer, MessageType.RAFT_LEADER_ANNOUNCE, payload)
            except Exception as exc:
                logger.debug(
                    "Failed to send leader announce",
                    peer=peer.node_id,
                    error=str(exc),
                )

    # ------------------------------------------------------------------
    # Peer helpers
    # ------------------------------------------------------------------

    def _get_peer_node_infos(self) -> List[NodeInfo]:
        """Return NodeInfo for all active cluster peers (excluding self)."""
        peers = []
        for member in self._membership.list_members(ClusterMemberStatus.ACTIVE):
            if member.node_id == self.node_id:
                continue
            peers.append(
                NodeInfo(
                    node_id=member.node_id,
                    host=member.description.host,
                    port=member.description.port,
                )
            )
        return peers

    # ------------------------------------------------------------------
    # Message handler registration
    # ------------------------------------------------------------------

    def _register_handlers(self) -> None:
        """Register all Raft protocol message handlers in the MessageBus router."""
        router = self._bus.router
        router.register(MessageType.RAFT_REQUEST_VOTE, _VoteRequestHandler(self))
        router.register(MessageType.RAFT_VOTE_RESPONSE, _VoteResponseHandler(self))
        router.register(MessageType.RAFT_APPEND_ENTRIES, _AppendEntriesHandler(self))
        router.register(MessageType.RAFT_APPEND_RESPONSE, _AppendResponseHandler(self))
        router.register(MessageType.RAFT_HEARTBEAT, _HeartbeatHandler(self))
        router.register(MessageType.RAFT_LEADER_ANNOUNCE, _LeaderAnnounceHandler(self))
        router.register(MessageType.RAFT_LOG_SYNC_REQUEST, _LogSyncRequestHandler(self))
        router.register(MessageType.RAFT_LOG_SYNC_RESPONSE, _LogSyncResponseHandler(self))


# ---------------------------------------------------------------------------
# Internal message handler implementations
# ---------------------------------------------------------------------------

class _VoteRequestHandler(MessageHandler):
    """Processes incoming RAFT_REQUEST_VOTE messages."""

    def __init__(self, service: ConsensusService) -> None:
        self._service = service

    async def handle(self, context: MessageContext) -> None:
        payload = context.payload or {}
        try:
            request = VoteRequest(**payload)
        except Exception as exc:
            logger.warning("Invalid VoteRequest payload", error=str(exc))
            return

        response = self._service._election.handle_vote_request(request)

        # Reply to sender
        reply_port = context.metadata.custom.get("reply_port", context.sender.port)
        reply_target = NodeInfo(
            node_id=context.sender.node_id,
            host=context.sender.host,
            port=reply_port,
        )
        reply_meta = MessageMetadata(
            correlation_id=context.metadata.request_id,
            custom={"type": "vote_response"},
        )
        await self._service._bus.send(
            reply_target,
            MessageType.RAFT_VOTE_RESPONSE,
            response.model_dump(),
            reply_meta,
        )


class _VoteResponseHandler(MessageHandler):
    """Processes incoming RAFT_VOTE_RESPONSE messages."""

    def __init__(self, service: ConsensusService) -> None:
        self._service = service

    async def handle(self, context: MessageContext) -> None:
        payload = context.payload or {}
        try:
            response = VoteResponse(**payload)
        except Exception as exc:
            logger.warning("Invalid VoteResponse payload", error=str(exc))
            return
        await self._service._election.tally_vote(response)


class _AppendEntriesHandler(MessageHandler):
    """Processes incoming RAFT_APPEND_ENTRIES messages (follower side)."""

    def __init__(self, service: ConsensusService) -> None:
        self._service = service

    async def handle(self, context: MessageContext) -> None:
        payload = context.payload or {}
        try:
            request = AppendEntriesRequest(**payload)
        except Exception as exc:
            logger.warning("Invalid AppendEntriesRequest payload", error=str(exc))
            return

        # Reset our election timer on valid AppendEntries
        self._service._election.cancel_election_timer()
        self._service._election.start_election_timer()

        response = self._service._replication.handle_append_entries(request)

        # Reply to sender (leader)
        reply_port = context.metadata.custom.get("reply_port", context.sender.port)
        reply_target = NodeInfo(
            node_id=context.sender.node_id,
            host=context.sender.host,
            port=reply_port,
        )
        reply_meta = MessageMetadata(correlation_id=context.metadata.request_id)
        await self._service._bus.send(
            reply_target,
            MessageType.RAFT_APPEND_RESPONSE,
            response.model_dump(),
            reply_meta,
        )


class _AppendResponseHandler(MessageHandler):
    """Processes incoming RAFT_APPEND_RESPONSE messages (leader side)."""

    def __init__(self, service: ConsensusService) -> None:
        self._service = service

    async def handle(self, context: MessageContext) -> None:
        payload = context.payload or {}
        try:
            response = AppendEntriesResponse(**payload)
        except Exception as exc:
            logger.warning("Invalid AppendEntriesResponse payload", error=str(exc))
            return

        peers = [
            m.node_id
            for m in self._service._membership.list_members(ClusterMemberStatus.ACTIVE)
        ]
        await self._service._replication.process_append_response(
            response, response.follower_id, peers
        )


class _HeartbeatHandler(MessageHandler):
    """Processes incoming RAFT_HEARTBEAT messages."""

    def __init__(self, service: ConsensusService) -> None:
        self._service = service

    async def handle(self, context: MessageContext) -> None:
        payload = context.payload or {}
        try:
            hb = HeartbeatPayload(**payload)
        except Exception as exc:
            logger.warning("Invalid HeartbeatPayload", error=str(exc))
            return

        # Update term and leader if needed
        if hb.term >= self._service._sm.current_term:
            self._service._sm.update_term(hb.term)
            self._service._sm.set_leader(hb.leader_id)

        # Reset election timer
        self._service._election.cancel_election_timer()
        self._service._election.start_election_timer()
        logger.debug("Heartbeat received", from_leader=hb.leader_id, term=hb.term)


class _LeaderAnnounceHandler(MessageHandler):
    """Processes incoming RAFT_LEADER_ANNOUNCE messages."""

    def __init__(self, service: ConsensusService) -> None:
        self._service = service

    async def handle(self, context: MessageContext) -> None:
        payload = context.payload or {}
        try:
            announce = LeaderAnnouncePayload(**payload)
        except Exception as exc:
            logger.warning("Invalid LeaderAnnouncePayload", error=str(exc))
            return

        old_term = self._service._sm.current_term
        if announce.term >= old_term:
            self._service._sm.update_term(announce.term)
            self._service._sm.set_leader(announce.leader_id)
            self._service._election.cancel_election_timer()
            self._service._election.start_election_timer()

            await self._service._events.publish(
                "consensus.leader.elected",
                {"leader_id": announce.leader_id, "term": announce.term},
            )
            if announce.term > old_term:
                await self._service._events.publish(
                    "consensus.term.changed",
                    {"old_term": old_term, "new_term": announce.term},
                )
        logger.info(
            "Leader announcement received",
            leader=announce.leader_id,
            term=announce.term,
        )


class _LogSyncRequestHandler(MessageHandler):
    """Responds to a follower's RAFT_LOG_SYNC_REQUEST with missing entries."""

    def __init__(self, service: ConsensusService) -> None:
        self._service = service

    async def handle(self, context: MessageContext) -> None:
        payload = context.payload or {}
        try:
            req = LogSyncRequest(**payload)
        except Exception as exc:
            logger.warning("Invalid LogSyncRequest payload", error=str(exc))
            return

        entries = self._service._log.get_range(req.from_index, self._service._log.last_index)
        response = LogSyncResponse(
            responder_id=self._service.node_id,
            entries=entries,
            commit_index=self._service._log.commit_index,
            correlation_id=req.request_id,
        )

        reply_port = context.metadata.custom.get("reply_port", context.sender.port)
        reply_target = NodeInfo(
            node_id=context.sender.node_id,
            host=context.sender.host,
            port=reply_port,
        )
        reply_meta = MessageMetadata(correlation_id=context.metadata.request_id)
        await self._service._bus.send(
            reply_target,
            MessageType.RAFT_LOG_SYNC_RESPONSE,
            response.model_dump(),
            reply_meta,
        )


class _LogSyncResponseHandler(MessageHandler):
    """Applies a RAFT_LOG_SYNC_RESPONSE to the local log (catch-up)."""

    def __init__(self, service: ConsensusService) -> None:
        self._service = service

    async def handle(self, context: MessageContext) -> None:
        payload = context.payload or {}
        try:
            resp = LogSyncResponse(**payload)
        except Exception as exc:
            logger.warning("Invalid LogSyncResponse payload", error=str(exc))
            return

        # Build a synthetic AppendEntriesRequest to reuse follower logic
        if resp.entries:
            first = resp.entries[0]
            synthetic = AppendEntriesRequest(
                leader_id=resp.responder_id,
                term=self._service._sm.current_term,
                prev_log_index=first.index - 1,
                prev_log_term=self._service._log.get_term_at(first.index - 1),
                entries=resp.entries,
                leader_commit=resp.commit_index,
            )
            self._service._replication.handle_append_entries(synthetic)
        logger.debug(
            "Log sync response applied",
            from_node=resp.responder_id,
            entries_count=len(resp.entries),
        )
