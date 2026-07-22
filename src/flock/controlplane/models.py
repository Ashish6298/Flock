"""Immutable Pydantic data models for the fleet management control plane."""

from __future__ import annotations

from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field


class FleetInfo(BaseModel):
    """Represents a fleet registry organizing multiple clusters."""
    fleet_id: str
    organization_id: str
    name: str
    metadata: Dict[str, str] = Field(default_factory=dict)

    model_config = {
        "frozen": True
    }


class EnrolledCluster(BaseModel):
    """Represents a member cluster registered within the management plane."""
    cluster_id: str
    fleet_id: str
    name: str
    version: str
    labels: Dict[str, str] = Field(default_factory=dict)
    features_active: List[str] = Field(default_factory=list)
    last_seen: float

    model_config = {
        "frozen": True
    }


class GovernancePolicy(BaseModel):
    """Security governance policy details enforced globally across clusters."""
    policy_id: str
    rule_name: str
    action_type: str  # "audit" or "enforce"
    parameters: Dict[str, Any] = Field(default_factory=dict)

    model_config = {
        "frozen": True
    }


class FleetUpgradePlan(BaseModel):
    """Plan defining target version rolling updates for enrolled clusters."""
    upgrade_id: str
    target_version: str
    batch_size: int
    state: str  # "scheduled", "running", "completed", "failed"
    cluster_states: Dict[str, str] = Field(default_factory=dict)

    model_config = {
        "frozen": True
    }


class MaintenanceWindow(BaseModel):
    """Represents scheduled cluster maintenance duration windows."""
    window_id: str
    cluster_id: str
    start_time: float
    end_time: float
    description: str

    model_config = {
        "frozen": True
    }


class FleetMetricsReport(BaseModel):
    """Aggregated status indices across all enrolled clusters in the fleet."""
    timestamp: float
    total_clusters: int
    active_clusters: int
    compliance_score: float
    upgrade_progress: float

    model_config = {
        "frozen": True
    }
