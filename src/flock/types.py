"""Common types, aliases, and data models used throughout Flock."""

import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Any, TypeAlias

NodeID: TypeAlias = str
TaskID: TypeAlias = str

class TaskStatus(str, Enum):
    """Represents the execution state of a distributed task."""
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"

@dataclass(frozen=True)
class NodeInfo:
    """Represents public metadata of a cluster node."""
    node_id: NodeID
    host: str
    port: int
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass(frozen=True)
class TaskSpec:
    """Defines the specifications of a task to be executed."""
    task_id: TaskID
    name: str
    args: tuple[Any, ...] = ()
    kwargs: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(cls, name: str, *args: Any, **kwargs: Any) -> "TaskSpec":
        """Helper to create a new task specification with a unique ID."""
        return cls(
            task_id=str(uuid.uuid4()),
            name=name,
            args=args,
            kwargs=kwargs
        )
