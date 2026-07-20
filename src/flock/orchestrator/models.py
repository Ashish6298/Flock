"""Orchestration Models."""

from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class ClusterPolicy(BaseModel):
    """Represents optimization rules guiding orchestration decisions."""
    policy_id: str
    strategy_name: str  # "balanced", "throughput", "low_latency"
    max_migration_rate: int = 5
    target_utilization: float = 70.0

    model_config = {
        "frozen": True
    }


class OptimizationPlan(BaseModel):
    """Represents calculated rebalancing target recommendations."""
    plan_id: str
    target_nodes: List[str]
    tasks_to_migrate: Dict[str, str]  # task_id -> target_node_id
    cost_score: float

    model_config = {
        "frozen": True
    }


class ScalingDecision(BaseModel):
    """Represents a scale-out or scale-in recommendation."""
    decision_id: str
    node_id: str
    scale_type: str  # "SCALE_OUT", "SCALE_IN"
    size_change: int
    timestamp: float

    model_config = {
        "frozen": True
    }


class MigrationPlan(BaseModel):
    """Represents target parameter limits for a scheduled task migration."""
    task_id: str
    source_node: str
    target_node: str
    pre_check_passed: bool

    model_config = {
        "frozen": True
    }


class SchedulingRecommendation(BaseModel):
    """Represents placement predictions for scheduler planning."""
    task_id: str
    recommended_node: str
    reasoning: str

    model_config = {
        "frozen": True
    }


class ClusterSnapshot(BaseModel):
    """Telemetry summary representation indicating cluster-wide conditions."""
    timestamp: float
    active_nodes: List[str]
    task_count: int
    avg_utilization: float

    model_config = {
        "frozen": True
    }
