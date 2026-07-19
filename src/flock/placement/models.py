"""Data models representing placement metrics, capabilities, and assignment records."""

from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional

class PlacementPolicy(str, Enum):
    """Policies dictating how healthy nodes are selected and prioritized."""
    FIRST_HEALTHY = "FIRST_HEALTHY"
    CAPABILITY_MATCH = "CAPABILITY_MATCH"

@dataclass(frozen=True)
class NodeCapability:
    """Immutable capabilities and resource specifications representing cluster node environments."""
    node_id: str
    cpu_count: int = 1
    cpu_arch: str = "x86_64"
    operating_system: str = "linux"
    python_version: str = "3.11"
    available_memory_mb: int = 1024
    supported_tags: List[str] = field(default_factory=list)
    custom_labels: Dict[str, Any] = field(default_factory=dict)

@dataclass(frozen=True)
class PlacementDecision:
    """Immutable record mapping a task to its selected placement target."""
    task_id: str
    selected_node_id: str
    policy_used: PlacementPolicy
    timestamp: float
    reason: str = "Default placement selection"

@dataclass(frozen=True)
class AssignmentRecord:
    """Immutable record tracking assignment metadata versions and acknowledgments."""
    task_id: str
    node_id: str
    assigned_timestamp: float
    acknowledged: bool = False
    version: int = 1
