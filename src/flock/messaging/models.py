"""Data models for message envelope structures, metadata, and contexts."""

import time
import uuid
from dataclasses import dataclass, field
from typing import Dict, Any, Optional
from flock.types import NodeInfo

@dataclass(frozen=True)
class MessageMetadata:
    """Standardized metadata containing routing, correlation, and diagnostics attributes."""
    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    protocol_version: int = 1
    correlation_id: Optional[str] = None
    request_id: Optional[str] = None
    timestamp: float = field(default_factory=time.time)
    ttl_seconds: Optional[float] = None
    priority: int = 0
    custom: Dict[str, Any] = field(default_factory=dict)

@dataclass
class MessageContext:
    """Execution environment for an incoming network message passed to handlers."""
    message_type: int
    payload: Any
    metadata: MessageMetadata
    sender: NodeInfo
    timestamp: float = field(default_factory=time.time)
    response_payload: Optional[Any] = None
