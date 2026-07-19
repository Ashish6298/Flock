"""Data models representing minimal identity for discovered peers."""

import time
from dataclasses import dataclass, field
from typing import Dict, Any, List

@dataclass(frozen=True)
class NodeDescription:
    """Immutable representation of a discovered remote node's static metadata."""
    node_id: str
    host: str
    port: int
    protocol_version: int = 1
    framework_version: str = "0.1.0"
    startup_timestamp: float = field(default_factory=time.time)
    capabilities: List[str] = field(default_factory=list)
    tags: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
