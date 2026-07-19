"""Immutable data models for the Flock Raft Consensus subsystem.

All models are validated using Pydantic v2 with strict typing.  Models that
represent protocol messages (VoteRequest, VoteResponse, AppendEntriesRequest,
AppendEntriesResponse) are serialisable to plain dictionaries so they can be
transmitted through the existing MessageBus/serializer pipeline without
coupling to the consensus internals.
"""

from __future__ import annotations

import time
import uuid
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, model_validator


# ---------------------------------------------------------------------------
# Role enumeration
# ---------------------------------------------------------------------------

class RaftRole(str, Enum):
    """Node participation role within the Raft protocol state machine."""

    FOLLOWER = "FOLLOWER"
    """Default state.  Responds to RPCs from leaders and candidates."""

    CANDIDATE = "CANDIDATE"
    """Transitional state during an election.  Solicits votes from peers."""

    LEADER = "LEADER"
    """Authoritative state.  Drives log replication and heartbeats."""


# ---------------------------------------------------------------------------
# Core state
# ---------------------------------------------------------------------------

class RaftNodeState(BaseModel):
    """Snapshot of a Raft node's durable and volatile state.

    Durable fields (current_term, voted_for) must be persisted to stable
    storage before responding to RPCs.  Phase 12 keeps these in-memory;
    Phase 13 will add persistence.

    Volatile fields (commit_index, last_applied) may be reconstructed from
    the durable log after a restart.
    """

    model_config = {"frozen": True}

    node_id: str
    """Stable identifier for this node across elections."""

    role: RaftRole = RaftRole.FOLLOWER
    """Current participation role."""

    current_term: int = 0
    """Monotonically increasing election term counter."""

    voted_for: Optional[str] = None
    """Candidate ID this node voted for in ``current_term``, or ``None``."""

    commit_index: int = 0
    """Index of the highest log entry known to be committed."""

    last_applied: int = 0
    """Index of the highest log entry applied to the state machine."""

    leader_id: Optional[str] = None
    """The node_id of the current known leader, or ``None``."""

    def with_updates(self, **kwargs: Any) -> "RaftNodeState":
        """Return a new ``RaftNodeState`` with selected fields replaced."""
        data = self.model_dump()
        data.update(kwargs)
        return RaftNodeState(**data)


# ---------------------------------------------------------------------------
# Log entry
# ---------------------------------------------------------------------------

class LogEntry(BaseModel):
    """A single entry in the replicated Raft log.

    ``command`` is intentionally opaque (``bytes``) so the consensus layer
    remains decoupled from application semantics.  Higher-level subsystems
    serialise their commands before submitting them through ConsensusService.
    """

    model_config = {"frozen": True}

    index: int
    """1-based position of this entry in the replicated log."""

    term: int
    """The election term in which the leader created this entry."""

    command: bytes = b""
    """Opaque application command payload."""

    entry_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    """Universally unique identifier for deduplication and tracing."""

    created_at: float = Field(default_factory=time.time)
    """Wall-clock timestamp when the leader created this entry."""

    @model_validator(mode="after")
    def validate_index_positive(self) -> "LogEntry":
        """Ensure index is at least 1 (Raft indices are 1-based)."""
        if self.index < 1:
            raise ValueError(f"LogEntry index must be >= 1, got {self.index}")
        return self

    @model_validator(mode="after")
    def validate_term_non_negative(self) -> "LogEntry":
        """Ensure term is non-negative."""
        if self.term < 0:
            raise ValueError(f"LogEntry term must be >= 0, got {self.term}")
        return self


# ---------------------------------------------------------------------------
# Term metadata
# ---------------------------------------------------------------------------

class TermInfo(BaseModel):
    """Metadata describing a single Raft election term."""

    model_config = {"frozen": True}

    term: int
    """The term number (monotonically increasing)."""

    leader_id: Optional[str] = None
    """Node ID of the elected leader, or ``None`` if not yet established."""

    start_timestamp: float = Field(default_factory=time.time)
    """Wall-clock time when this term began (on this node)."""


# ---------------------------------------------------------------------------
# Election RPC messages
# ---------------------------------------------------------------------------

class VoteRequest(BaseModel):
    """RequestVote RPC arguments sent by a candidate to all peers.

    Implements the log completeness check from Raft §5.4: a candidate's log
    must be at least as up-to-date as any other node for that node to grant a
    vote.
    """

    model_config = {"frozen": True}

    candidate_id: str
    """Node ID of the candidate requesting votes."""

    term: int
    """Candidate's current term."""

    last_log_index: int = 0
    """Index of candidate's last log entry (0 if log is empty)."""

    last_log_term: int = 0
    """Term of candidate's last log entry (0 if log is empty)."""

    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    """Correlation ID for matching responses."""


class VoteResponse(BaseModel):
    """RequestVote RPC reply sent by a follower back to the candidate."""

    model_config = {"frozen": True}

    voter_id: str
    """Node ID of the responding voter."""

    term: int
    """Voter's current term (for the candidate to update itself if stale)."""

    vote_granted: bool
    """``True`` if the vote was granted to the candidate."""

    reason: str = ""
    """Human-readable explanation when ``vote_granted`` is ``False``."""

    correlation_id: str = ""
    """Echoed ``request_id`` from the original VoteRequest."""


# ---------------------------------------------------------------------------
# Replication RPC messages
# ---------------------------------------------------------------------------

class AppendEntriesRequest(BaseModel):
    """AppendEntries RPC arguments sent by the leader to followers.

    An AppendEntries RPC with an empty ``entries`` list serves as a
    heartbeat, resetting the follower's election timer without modifying
    its log.
    """

    model_config = {"frozen": True}

    leader_id: str
    """Node ID of the leader issuing this RPC."""

    term: int
    """Leader's current term."""

    prev_log_index: int = 0
    """Index of the log entry immediately preceding the new entries."""

    prev_log_term: int = 0
    """Term of the ``prev_log_index`` entry (0 if ``prev_log_index`` is 0)."""

    entries: List[LogEntry] = Field(default_factory=list)
    """Ordered log entries to append.  Empty for heartbeats."""

    leader_commit: int = 0
    """Leader's current commit index."""

    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    """Correlation ID for matching responses."""


class AppendEntriesResponse(BaseModel):
    """AppendEntries RPC reply sent by a follower to the leader."""

    model_config = {"frozen": True}

    follower_id: str
    """Node ID of the responding follower."""

    term: int
    """Follower's current term (for the leader to step down if stale)."""

    success: bool
    """``True`` if the follower accepted and appended the entries."""

    match_index: int = 0
    """Highest log index known to be replicated on this follower."""

    conflict_index: int = 0
    """First conflicting index (optimises log back-tracking on failure)."""

    conflict_term: int = 0
    """Term of the conflicting entry at ``conflict_index``."""

    correlation_id: str = ""
    """Echoed ``request_id`` from the original AppendEntriesRequest."""


# ---------------------------------------------------------------------------
# Election outcome
# ---------------------------------------------------------------------------

class ElectionResult(BaseModel):
    """Summary of a completed leader election."""

    model_config = {"frozen": True}

    term: int
    """The term in which the election was conducted."""

    winner_id: str
    """Node ID of the elected leader."""

    votes_received: int
    """Number of votes collected by the winner."""

    quorum_size: int
    """Minimum votes required for election (``cluster_size // 2 + 1``)."""

    elected_at_timestamp: float = Field(default_factory=time.time)
    """Wall-clock time when the leader was declared."""


# ---------------------------------------------------------------------------
# Heartbeat payload
# ---------------------------------------------------------------------------

class HeartbeatPayload(BaseModel):
    """Payload for a Raft heartbeat (empty AppendEntries) message.

    Transmitted periodically by the leader to prevent follower timeouts.
    """

    model_config = {"frozen": True}

    leader_id: str
    """Node ID of the sending leader."""

    term: int
    """Leader's current term."""

    commit_index: int = 0
    """Leader's current commit index, so followers can advance their own."""

    timestamp: float = Field(default_factory=time.time)
    """Wall-clock time when the heartbeat was emitted."""


# ---------------------------------------------------------------------------
# Leader announcement payload
# ---------------------------------------------------------------------------

class LeaderAnnouncePayload(BaseModel):
    """Broadcast payload sent by a new leader upon election.

    All nodes receiving this message update their known leader and reset
    their election timers.
    """

    model_config = {"frozen": True}

    leader_id: str
    """Node ID of the newly elected leader."""

    term: int
    """The term for which leadership is being announced."""

    timestamp: float = Field(default_factory=time.time)
    """Wall-clock time of the announcement."""


# ---------------------------------------------------------------------------
# Log sync messages (used for catch-up replication)
# ---------------------------------------------------------------------------

class LogSyncRequest(BaseModel):
    """Request sent by a lagging follower to retrieve missing log entries."""

    model_config = {"frozen": True}

    requester_id: str
    """Node ID of the requesting follower."""

    from_index: int
    """First log index needed (inclusive)."""

    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    """Correlation ID."""


class LogSyncResponse(BaseModel):
    """Response from the leader containing requested log entries."""

    model_config = {"frozen": True}

    responder_id: str
    """Node ID of the responding leader."""

    entries: List[LogEntry] = Field(default_factory=list)
    """Ordered log entries starting at ``from_index``."""

    commit_index: int = 0
    """Leader's current commit index."""

    correlation_id: str = ""
    """Echoed ``request_id`` from the LogSyncRequest."""


# ---------------------------------------------------------------------------
# Public surface
# ---------------------------------------------------------------------------

__all__ = [
    "RaftRole",
    "RaftNodeState",
    "LogEntry",
    "TermInfo",
    "VoteRequest",
    "VoteResponse",
    "AppendEntriesRequest",
    "AppendEntriesResponse",
    "ElectionResult",
    "HeartbeatPayload",
    "LeaderAnnouncePayload",
    "LogSyncRequest",
    "LogSyncResponse",
]
