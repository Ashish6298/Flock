"""Data models representing health status states and record entries."""

from enum import Enum
from dataclasses import dataclass

class HealthState(str, Enum):
    """Reachability and health states representing node status inside a cluster."""
    UNKNOWN = "UNKNOWN"
    HEALTHY = "HEALTHY"
    SUSPECTED = "SUSPECTED"
    UNREACHABLE = "UNREACHABLE"
    RECOVERING = "RECOVERING"

@dataclass(frozen=True)
class HealthRecord:
    """Immutable representation of a node's reachability health metrics."""
    node_id: str
    state: HealthState
    last_heartbeat_timestamp: float
    missed_heartbeats_count: int = 0
    round_trip_time_ms: float = 0.0
    sequence_id: int = 0
