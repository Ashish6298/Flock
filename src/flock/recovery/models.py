"""Data models representing retry policies, contexts, and recovery plans."""

from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

class BackoffStrategy(str, Enum):
    """Backoff delay calculation algorithms."""
    FIXED = "FIXED"
    LINEAR = "LINEAR"
    EXPONENTIAL = "EXPONENTIAL"
    EXPONENTIAL_JITTER = "EXPONENTIAL_JITTER"
    IMMEDIATE = "IMMEDIATE"

@dataclass(frozen=True)
class RetryPolicy:
    """Immutable configuration defining task retry criteria."""
    max_attempts: int = 3
    base_delay_sec: float = 1.0
    backoff_strategy: BackoffStrategy = BackoffStrategy.FIXED
    max_delay_sec: float = 60.0
    retryable_exceptions: List[str] = field(default_factory=list)
    non_retryable_exceptions: List[str] = field(default_factory=list)

@dataclass(frozen=True)
class RetryContext:
    """Tracks retry history progress for a task."""
    task_id: str
    attempt_count: int = 0
    last_attempt_timestamp: float = 0.0
    last_worker_id: Optional[str] = None
    last_error_message: Optional[str] = None

@dataclass(frozen=True)
class RetryDecision:
    """Immutable verdict of retry evaluation checks."""
    should_retry: bool
    delay_sec: float = 0.0
    reason: str = ""

@dataclass(frozen=True)
class RecoveryPlan:
    """Complete failover assignment script."""
    task_id: str
    target_node_id: str
    exclude_workers: List[str] = field(default_factory=list)
    cooldown_until: float = 0.0


class ClusterSnapshot(BaseModel):
    """Represents a consistent snapshot of the cluster state Machine."""
    snapshot_id: str
    timestamp: float
    state_hash: str
    metadata: Dict[str, str] = Field(default_factory=dict)
    data: Dict[str, Any] = Field(default_factory=dict)

    model_config = {
        "frozen": True
    }


class BackupArchive(BaseModel):
    """Represents a compiled, optionally encrypted backup archive descriptor."""
    backup_id: str
    snapshot_id: str
    timestamp: float
    backup_type: str  # "full" or "incremental"
    checksum: str
    signature: str
    encrypted: bool
    data_size: int
    metadata: Dict[str, str] = Field(default_factory=dict)

    model_config = {
        "frozen": True
    }


class CheckpointDescriptor(BaseModel):
    """Represents a synchronized cluster-wide distributed checkpoint."""
    checkpoint_id: str
    sequence_number: int
    timestamp: float
    coordinator_node_id: str
    snapshot_id: str
    integrity_signature: str

    model_config = {
        "frozen": True
    }


class RetentionPolicy(BaseModel):
    """Configurable backup retention parameters."""
    policy_id: str
    max_backups_retained: int = 10
    ttl_seconds: float = 86400.0 * 30  # 30 days
    archive_on_eviction: bool = False

    model_config = {
        "frozen": True
    }


class RecoveryMetricsReport(BaseModel):
    """Telemetry report summarizing disaster recovery operation performance."""
    total_snapshots_taken: int
    total_backups_created: int
    total_restores_executed: int
    last_backup_timestamp: Optional[float] = None
    last_restore_timestamp: Optional[float] = None
    health_status: str  # "HEALTHY", "DEGRADED", "CRITICAL"

    model_config = {
        "frozen": True
    }

