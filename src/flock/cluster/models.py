"""Data models representing cluster membership status and state records."""

import time
from enum import Enum
from dataclasses import dataclass
from flock.discovery.models import NodeDescription

class ClusterMemberStatus(str, Enum):
    """Membership status states representing node lifecycle inside a cluster."""
    UNKNOWN = "UNKNOWN"
    JOINING = "JOINING"
    ACTIVE = "ACTIVE"
    LEAVING = "LEAVING"
    REMOVED = "REMOVED"
    REJECTED = "REJECTED"

@dataclass(frozen=True)
class ClusterMember:
    """Immutable representation of a node's membership profile and metadata version."""
    node_id: str
    description: NodeDescription
    status: ClusterMemberStatus
    join_timestamp: float
    membership_version: int = 1
    role: str = "worker"
