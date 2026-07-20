"""Federation Models."""

from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class FederationCluster(BaseModel):
    """Represents a member cluster registered within the global federation."""
    cluster_id: str
    name: str
    endpoints: List[str]
    is_healthy: bool
    capacity_score: float

    model_config = {
        "frozen": True
    }


class FederationNode(BaseModel):
    """Represents a node that belongs to a specific cluster."""
    node_id: str
    cluster_id: str
    role: str

    model_config = {
        "frozen": True
    }


class GlobalTask(BaseModel):
    """Represents a task scheduled across cluster boundaries."""
    task_id: str
    payload: bytes
    required_capabilities: List[str] = Field(default_factory=list)
    target_cluster_id: Optional[str] = None

    model_config = {
        "frozen": True
    }


class RoutingDecision(BaseModel):
    """Represents the global routing choice for a task."""
    decision_id: str
    task_id: str
    source_cluster: str
    destination_cluster: str

    model_config = {
        "frozen": True
    }


class ReplicationPolicy(BaseModel):
    """Represents cross-cluster metadata sync configurations."""
    policy_id: str
    sync_interval_seconds: int = 300
    max_retry_count: int = 3

    model_config = {
        "frozen": True
    }


class FederationHealth(BaseModel):
    """Overall status metric summary for the entire federation link."""
    status: str  # "HEALTHY", "DEGRADED", "UNHEALTHY"
    cluster_healths: Dict[str, bool]

    model_config = {
        "frozen": True
    }


class FederationSnapshot(BaseModel):
    """Replicated global state snapshot."""
    timestamp: float
    cluster_count: int
    total_nodes: int
    global_task_count: int

    model_config = {
        "frozen": True
    }


class ClusterAdvertisement(BaseModel):
    """Payload representing periodic capacity announcements sent by member clusters."""
    cluster_id: str
    timestamp: float
    resource_summary: Dict[str, float]

    model_config = {
        "frozen": True
    }
