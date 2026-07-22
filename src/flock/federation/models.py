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


class TrustRelationship(BaseModel):
    """Federation cryptographic trust definition and exchange payload."""
    local_cluster_id: str
    remote_cluster_id: str
    certificate_pem: str
    signature: str
    established_at: float
    valid_until: float

    model_config = {
        "frozen": True
    }


class FederationTopology(BaseModel):
    """Discovered geographical and network cluster layout of the hybrid mesh."""
    topology_id: str
    timestamp: float
    clusters: List[FederationCluster] = Field(default_factory=list)
    latency_matrix: Dict[str, Dict[str, float]] = Field(default_factory=dict)  # cluster_id -> target_id -> latency_ms

    model_config = {
        "frozen": True
    }


class FederationPolicy(BaseModel):
    """Security, access, and routing policies enforced globally across clusters."""
    policy_id: str
    target_clusters: List[str]  # Cluster IDs or ["*"]
    allowed_actions: List[str]
    max_cross_region_latency_ms: float = 300.0

    model_config = {
        "frozen": True
    }


class FederationMetricsReport(BaseModel):
    """Aggregated cross-cluster performance indicators and health telemetry."""
    timestamp: float
    active_clusters_count: int
    remote_executions_count: int
    replication_delay_seconds: float
    failover_success_count: int

    model_config = {
        "frozen": True
    }

