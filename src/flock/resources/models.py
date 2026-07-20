"""Resource Models."""

from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class NodeResourceProfile(BaseModel):
    """Represents a node's resource capacities and current utilization levels."""
    node_id: str
    cpu_cores: float
    cpu_util: float  # percentage 0.0 - 100.0
    memory_mb: float
    memory_util: float  # percentage
    gpu_cores: float = 0.0
    gpu_util: float = 0.0

    model_config = {
        "frozen": True
    }


class ResourceReservation(BaseModel):
    """Represents an active resource reservation lease."""
    reservation_id: str
    node_id: str
    request_id: str
    resources: Dict[str, float]
    expires_at: float

    model_config = {
        "frozen": True
    }


class AllocationResult(BaseModel):
    """Represents the outcome of a resource allocation request."""
    success: bool
    reservation_id: Optional[str] = None
    assigned_node: Optional[str] = None
    allocated_resources: Dict[str, float] = Field(default_factory=dict)

    model_config = {
        "frozen": True
    }


class WorkloadClassification(BaseModel):
    """Represents policy parameters classifying incoming task footprints."""
    class_id: str
    priority: int
    resource_limit: Dict[str, float]

    model_config = {
        "frozen": True
    }


class BalancingDecision(BaseModel):
    """Represents a workload migration balancing recommendation."""
    recommendation_id: str
    source_node: str
    target_node: str
    task_id: str

    model_config = {
        "frozen": True
    }


class CapacityForecast(BaseModel):
    """Exposes cluster capacity calculations and exhaustion timelines."""
    exhaustion_timestamp: float
    forecast_growth_rate: float
    alerts: List[str] = Field(default_factory=list)

    model_config = {
        "frozen": True
    }
