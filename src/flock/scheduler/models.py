"""Data models representing distributed task configurations and scheduling states."""

from enum import Enum, IntEnum
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List

class TaskPriority(IntEnum):
    """Priority levels for ordering tasks in scheduling queues."""
    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3

class TaskStatus(str, Enum):
    """Scheduling states representing a task's progress through the scheduler."""
    CREATED = "CREATED"
    VALIDATED = "VALIDATED"
    QUEUED = "QUEUED"
    ANNOUNCED = "ANNOUNCED"
    PLACEMENT_PENDING = "PLACEMENT_PENDING"
    ASSIGNED = "ASSIGNED"
    CANCELLED = "CANCELLED"
    EXPIRED = "EXPIRED"
    FAILED = "FAILED"
    COMPLETED = "COMPLETED"

class SchedulingPolicy(str, Enum):
    """Policies dictating how tasks are ordered in queues."""
    FIFO = "FIFO"
    PRIORITY = "PRIORITY"

@dataclass(frozen=True)
class RetryPolicy:
    """Policy for retrying failed executions."""
    max_retries: int = 3
    initial_delay_sec: float = 1.0
    backoff_multiplier: float = 2.0

@dataclass(frozen=True)
class TaskConstraints:
    """Requirements dictating node execution environment."""
    required_capabilities: List[str] = field(default_factory=list)
    custom_constraints: Dict[str, Any] = field(default_factory=dict)

@dataclass(frozen=True)
class TaskMetadata:
    """Scheduling configuration and constraints wrapper."""
    priority: TaskPriority = TaskPriority.NORMAL
    scheduling_policy: SchedulingPolicy = SchedulingPolicy.FIFO
    retry_policy: RetryPolicy = field(default_factory=RetryPolicy)
    constraints: TaskConstraints = field(default_factory=TaskConstraints)
    expiration_timestamp: Optional[float] = None
    execution_deadline: Optional[float] = None

@dataclass(frozen=True)
class Task:
    """Immutable representation of a task description and scheduling metrics."""
    task_id: str
    creator_node_id: str
    payload: Dict[str, Any]
    metadata: TaskMetadata = field(default_factory=TaskMetadata)
    status: TaskStatus = TaskStatus.CREATED
    creation_timestamp: float = 0.0
