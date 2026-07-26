"""Deployment Subsystem Models."""

import time
from enum import Enum
from typing import Dict, List, Optional, Protocol
from pydantic import BaseModel, Field


class DeploymentStatus(str, Enum):
    """Lifecycle enums representing deployment status state transitions."""
    CREATED = "CREATED"
    VALIDATED = "VALIDATED"
    PREPARED = "PREPARED"
    DEPLOYING = "DEPLOYING"
    RUNNING = "RUNNING"
    UPDATING = "UPDATING"
    STOPPING = "STOPPING"
    STOPPED = "STOPPED"
    FAILED = "FAILED"
    ROLLED_BACK = "ROLLED_BACK"


class DeploymentTarget(str, Enum):
    """Enums representing the deployment environment target types."""
    LOCAL = "LOCAL"
    DOCKER = "DOCKER"
    DOCKER_COMPOSE = "DOCKER_COMPOSE"
    KUBERNETES = "KUBERNETES"
    CLOUD = "CLOUD"


class DeploymentResources(BaseModel):
    """System resource request limits for CPU and RAM utilization."""
    cpu_request: Optional[str] = None
    cpu_limit: Optional[str] = None
    memory_request: Optional[str] = None
    memory_limit: Optional[str] = None

    model_config = {"frozen": True}


class DeploymentEnvironment(BaseModel):
    """Environment contexts mapping variables and vault secrets context details."""
    env_vars: Dict[str, str] = Field(default_factory=dict)
    secrets: Dict[str, str] = Field(default_factory=dict)

    model_config = {"frozen": True}


class DeploymentConfiguration(BaseModel):
    """Reusable layout options mapping ports, volumes, and network settings."""
    ports: List[int] = Field(default_factory=list)
    volumes: List[str] = Field(default_factory=list)
    networks: List[str] = Field(default_factory=list)
    resources: DeploymentResources = Field(default_factory=DeploymentResources)
    labels: Dict[str, str] = Field(default_factory=dict)
    annotations: Dict[str, str] = Field(default_factory=dict)

    model_config = {"frozen": True}


class DeploymentMetadata(BaseModel):
    """Operational metadata labels tracking author descriptions."""
    created_by: str = "system"
    description: Optional[str] = None

    model_config = {"frozen": True}


class DeploymentHealth(BaseModel):
    """Health indicators tracking checking parameters."""
    status: str = "UNKNOWN"  # "HEALTHY", "WARNING", "DEGRADED", "FAILED", "UNKNOWN"
    message: str = ""
    timestamp: float = Field(default_factory=time.time)
    checks_performed: List[str] = Field(default_factory=list)

    model_config = {"frozen": True}


class Deployment(BaseModel):
    """Primary central source of truth for deployment setups."""
    deployment_id: str
    name: str
    target: DeploymentTarget
    config: DeploymentConfiguration
    env: DeploymentEnvironment
    status: DeploymentStatus = DeploymentStatus.CREATED
    metadata: DeploymentMetadata = Field(default_factory=DeploymentMetadata)
    health: DeploymentHealth = Field(default_factory=DeploymentHealth)

    model_config = {"frozen": True}


# ------------------------------------------------------------------
# Backward Compatibility Models
# ------------------------------------------------------------------

class DeploymentDefinition(BaseModel):
    """Represents core deployment spec coordinates (Legacy structure)."""
    deployment_id: str
    name: str
    namespace: str = "default"
    image: str
    replicas: int = 1
    env: Dict[str, str] = Field(default_factory=dict)

    model_config = {"frozen": True}


class DeploymentRevision(BaseModel):
    """Represents a specific revision history state snapshot (Legacy structure)."""
    revision_id: int
    deployment_id: str
    manifest: Dict[str, str] = Field(default_factory=dict)
    created_at: float

    model_config = {"frozen": True}


class RolloutState(BaseModel):
    """Represents rollout tracking metrics details (Legacy structure)."""
    deployment_id: str
    strategy: str  # "CANARY", "BLUE_GREEN", "ROLLING"
    batch_size: int = 1
    progress_percentage: float = 0.0
    status: str = "PENDING"  # "PENDING", "IN_PROGRESS", "COMPLETED", "FAILED"

    model_config = {"frozen": True}


class InfrastructureTemplate(BaseModel):
    """Represents input templates configuration blueprints (Legacy structure)."""
    template_id: str
    provider: str  # "KUBERNETES", "DOCKER_COMPOSE"
    contents: str

    model_config = {"frozen": True}


# ------------------------------------------------------------------
# Rollback Abstractions
# ------------------------------------------------------------------

class RollbackPolicy(str, Enum):
    """Enums representing automatic or manual rollback strategies."""
    IMMEDIATE = "IMMEDIATE"
    MANUAL = "MANUAL"


class RollbackMetadata(BaseModel):
    """Rollback execution details tracking reason."""
    reason: str
    triggered_by: str = "system"
    timestamp: float = Field(default_factory=time.time)

    model_config = {"frozen": True}


class RollbackRequest(BaseModel):
    """Request representation indicating target revision index."""
    deployment_id: str
    target_revision_id: int
    policy: RollbackPolicy = RollbackPolicy.IMMEDIATE
    metadata: RollbackMetadata

    model_config = {"frozen": True}


class RollbackHistory(BaseModel):
    """Logs database item record representing rollbacks execution logs."""
    rollback_id: str
    deployment_id: str
    previous_revision_id: int
    restored_revision_id: int
    status: str = "COMPLETED"  # "COMPLETED", "FAILED"

    model_config = {"frozen": True}


class IRollbackExecutor(Protocol):
    """Protocol interface defining execution endpoints for rollbacks."""

    def rollback(self, request: RollbackRequest) -> RollbackHistory:
        """Execute rollback pipeline snapshot restoration."""
        ...


# ------------------------------------------------------------------
# Validation Framework
# ------------------------------------------------------------------

class ValidationResult(BaseModel):
    """Validation report status tracking constraints compliance."""
    is_valid: bool
    errors: List[str] = Field(default_factory=list)

    model_config = {"frozen": True}


class DeploymentValidator:
    """Routines validating deployment options, network ports, and names."""

    @staticmethod
    def validate_deployment(deployment: Deployment) -> ValidationResult:
        """Validate naming specs, duplicate ports, and resource formats."""
        errors: List[str] = []
        
        # 1. Naming validations
        if not deployment.name or len(deployment.name) < 3:
            errors.append("Deployment name must be at least 3 characters long.")
            
        # 2. Port conflict validations
        ports = deployment.config.ports
        if len(ports) != len(set(ports)):
            errors.append("Duplicate ports detected in deployment configuration.")
        for p in ports:
            if p < 1 or p > 65535:
                errors.append(f"Port {p} is out of valid range (1-65535).")

        # 3. CPU/Memory validation (just checking they aren't negative or empty if specified)
        res = deployment.config.resources
        if res.cpu_limit and res.cpu_limit.startswith("-"):
            errors.append("CPU limit cannot be negative.")
        if res.memory_limit and res.memory_limit.startswith("-"):
            errors.append("Memory limit cannot be negative.")

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors
        )


class RollbackResult(BaseModel):
    """Execution status output report details."""
    success: bool
    message: str
    previous_revision_id: int
    restored_revision_id: int
    timestamp: float = Field(default_factory=time.time)

    model_config = {"frozen": True}


class DeploymentSnapshot(BaseModel):
    """Configuration history catalog state snapshot representation."""
    deployment_id: str
    revision_id: int
    configuration: DeploymentConfiguration
    status: DeploymentStatus
    timestamp: float = Field(default_factory=time.time)

    model_config = {"frozen": True}


class ReleaseMetadata(BaseModel):
    """Tracking fields identifying tags environment settings."""
    release_id: str
    version: str
    environment: str
    created_at: float = Field(default_factory=time.time)

    model_config = {"frozen": True}


class ReleaseVerificationResult(BaseModel):
    """Post-deployment safety verification outcomes report."""
    release_id: str
    is_healthy: bool
    checks_passed: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)

    model_config = {"frozen": True}


class DeploymentCheckpoint(BaseModel):
    """Historical checkpoint markers for atomic rollback triggers."""
    checkpoint_id: str
    deployment_id: str
    state_hash: str
    timestamp: float = Field(default_factory=time.time)

    model_config = {"frozen": True}


class RollbackExecutionSummary(BaseModel):
    """Detailed summary tracking executed steps details."""
    rollback_id: str
    duration_ms: float
    strategy_used: str
    audit_trail: List[str] = Field(default_factory=list)

    model_config = {"frozen": True}


class DeploymentAuditRecord(BaseModel):
    """Audit logs tracing administrative transitions details."""
    record_id: str
    action: str  # "CREATE", "UPDATE", "ROLLBACK"
    user: str
    details: str
    timestamp: float = Field(default_factory=time.time)

    model_config = {"frozen": True}

