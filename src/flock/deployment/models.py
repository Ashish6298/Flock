"""Deployment Subsystem Models."""

from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class DeploymentDefinition(BaseModel):
    """Represents core deployment spec coordinates."""
    deployment_id: str
    name: str
    namespace: str = "default"
    image: str
    replicas: int = 1
    env: Dict[str, str] = Field(default_factory=dict)

    model_config = {
        "frozen": True
    }


class DeploymentRevision(BaseModel):
    """Represents a specific revision history state snapshot."""
    revision_id: int
    deployment_id: str
    manifest: Dict[str, str] = Field(default_factory=dict)
    created_at: float

    model_config = {
        "frozen": True
    }


class RolloutState(BaseModel):
    """Represents rollout tracking metrics details."""
    deployment_id: str
    strategy: str  # "CANARY", "BLUE_GREEN", "ROLLING"
    batch_size: int = 1
    progress_percentage: float = 0.0
    status: str = "PENDING"  # "PENDING", "IN_PROGRESS", "COMPLETED", "FAILED"

    model_config = {
        "frozen": True
    }


class InfrastructureTemplate(BaseModel):
    """Represents input templates configuration blueprints."""
    template_id: str
    provider: str  # "KUBERNETES", "DOCKER_COMPOSE"
    contents: str

    model_config = {
        "frozen": True
    }
