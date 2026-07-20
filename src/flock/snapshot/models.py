"""Snapshot models."""

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, ConfigDict


class SnapshotMetadata(BaseModel):
    """Metadata for a single snapshot file."""
    snapshot_id: str
    applied_index: int
    current_term: int
    timestamp: float
    checksum: str
    size_bytes: int

    model_config = {
        "frozen": True
    }


class SnapshotManifest(BaseModel):
    """Manifest describing all chunks of a snapshot."""
    snapshot_id: str
    metadata: SnapshotMetadata
    total_chunks: int
    chunk_size_bytes: int
    checksums: List[str]

    model_config = {
        "frozen": True
    }


class SnapshotChunk(BaseModel):
    """A single packet chunk of state machine snapshot data."""
    snapshot_id: str
    chunk_index: int
    data: bytes
    checksum: str

    model_config = {
        "frozen": True
    }


class SnapshotTransferSession(BaseModel):
    """Session tracker for active incremental transfer of snapshot chunks."""
    model_config = ConfigDict(arbitrary_types_allowed=True)

    session_id: str
    snapshot_id: str
    peer_id: str
    total_chunks: int
    next_chunk_index: int
    chunks_received: Dict[int, bytes] = Field(default_factory=dict)
    is_completed: bool = False
    is_failed: bool = False


class SnapshotInstallRequest(BaseModel):
    """InstallSnapshot consensus message payload (Raft §7)."""
    leader_id: str
    term: int
    last_included_index: int
    last_included_term: int
    metadata: SnapshotMetadata
    manifest: SnapshotManifest

    model_config = {
        "frozen": True
    }


class SnapshotInstallResponse(BaseModel):
    """InstallSnapshot response payload from follower to leader."""
    follower_id: str
    term: int
    success: bool
    last_applied_index: int

    model_config = {
        "frozen": True
    }


class SnapshotRestoreResult(BaseModel):
    """Status details returned post-restoration."""
    snapshot_id: str
    applied_index: int
    term: int
    timestamp: float
    success: bool

    model_config = {
        "frozen": True
    }


class CompactionStatistics(BaseModel):
    """Metadata summarizing log compaction execution details."""
    last_included_index: int
    last_included_term: int
    entries_truncated: int
    timestamp: float

    model_config = {
        "frozen": True
    }
