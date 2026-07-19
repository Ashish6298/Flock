"""Data models representing worker details and execution progress states."""

from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, Any, List

class ExecutionState(str, Enum):
    """Local runtime execution progress lifecycle states."""
    ASSIGNED = "ASSIGNED"
    ACCEPTED = "ACCEPTED"
    PREPARING = "PREPARING"
    QUEUED = "QUEUED"
    STARTING = "STARTING"
    RUNNING = "RUNNING"
    CANCELLING = "CANCELLING"
    CANCELLED = "CANCELLED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

@dataclass(frozen=True)
class WorkerInfo:
    """Immutable metadata describing a local execution worker thread or process."""
    worker_id: str
    supported_capabilities: List[str] = field(default_factory=list)
    executor_type: str = "thread"
    active_tasks: int = 0
    startup_timestamp: float = 0.0
