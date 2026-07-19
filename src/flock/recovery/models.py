"""Data models representing retry policies, contexts, and recovery plans."""

from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional

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
