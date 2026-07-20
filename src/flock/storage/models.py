"""Storage models."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class WALEntry(BaseModel):
    """Represents a Write-Ahead Log entry."""
    index: int
    term: int
    command_id: str
    payload: bytes
    timestamp: float
    checksum: str

    model_config = {
        "frozen": True
    }


class WALSegment(BaseModel):
    """Represents metadata for a single log file segment."""
    segment_id: str
    start_index: int
    end_index: int
    size_bytes: int
    is_active: bool

    model_config = {
        "frozen": True
    }


class StorageMetadata(BaseModel):
    """Persisted metadata containing term tracking details."""
    node_id: str
    current_term: int
    voted_for: Optional[str] = None
    last_applied_index: int = 0

    model_config = {
        "frozen": True
    }


class RecoveryCheckpoint(BaseModel):
    """Marks a transaction log checkpoint boundary."""
    snapshot_id: str
    last_included_index: int
    last_included_term: int
    wal_offset: int

    model_config = {
        "frozen": True
    }


class PersistentState(BaseModel):
    """Encapsulates persistent state mapping."""
    metadata: StorageMetadata
    checkpoint: Optional[RecoveryCheckpoint] = None

    model_config = {
        "frozen": True
    }


class StorageStatistics(BaseModel):
    """Dynamic stats summarizing disk state properties."""
    total_entries_written: int
    segment_count: int
    size_on_disk_bytes: int

    model_config = {
        "frozen": True
    }


class WALReplayResult(BaseModel):
    """Replay summary report details."""
    entries_replayed: int
    success: bool
    duration_seconds: float

    model_config = {
        "frozen": True
    }


class StorageConfiguration(BaseModel):
    """Configuration constraints for storage engine."""
    data_directory: str
    max_segment_size_bytes: int = 10 * 1024 * 1024  # 10MB
    sync_on_write: bool = True

    model_config = {
        "frozen": True
    }


class StorageHealthReport(BaseModel):
    """Storage health report details."""
    is_healthy: bool
    total_segments: int
    error_message: Optional[str] = None

    model_config = {
        "frozen": True
    }
