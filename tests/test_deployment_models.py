"""Unit tests for new deployment models, validation framework, and health abstractions."""

import time
import pytest
from flock.deployment.models import (
    Deployment,
    DeploymentConfiguration,
    DeploymentEnvironment,
    DeploymentHealth,
    DeploymentResources,
    DeploymentStatus,
    DeploymentTarget,
    DeploymentValidator,
    RollbackMetadata,
    RollbackPolicy,
    RollbackRequest,
)


def test_deployment_models_and_validation() -> None:
    res = DeploymentResources(
        cpu_request="100m",
        cpu_limit="200m",
        memory_request="128Mi",
        memory_limit="256Mi",
    )
    env = DeploymentEnvironment(
        env_vars={"KEY": "VALUE"},
        secrets={"PASSWORD": "supersecret"},
    )
    cfg = DeploymentConfiguration(
        ports=[80, 443],
        volumes=["/data:/var/data"],
        networks=["flock-mesh"],
        resources=res,
        labels={"app": "test"},
    )
    dep = Deployment(
        deployment_id="dep-uuid-001",
        name="api-gateway",
        target=DeploymentTarget.DOCKER,
        config=cfg,
        env=env,
        status=DeploymentStatus.CREATED,
    )

    # 1. Check fields
    assert dep.deployment_id == "dep-uuid-001"
    assert dep.config.ports == [80, 443]
    assert dep.env.env_vars["KEY"] == "VALUE"
    assert dep.status == DeploymentStatus.CREATED

    # 2. Run validator
    val_res = DeploymentValidator.validate_deployment(dep)
    assert val_res.is_valid is True
    assert len(val_res.errors) == 0


def test_deployment_validation_failures() -> None:
    # 1. Invalid short name
    cfg = DeploymentConfiguration()
    env = DeploymentEnvironment()
    dep = Deployment(
        deployment_id="dep-002",
        name="ab",
        target=DeploymentTarget.LOCAL,
        config=cfg,
        env=env,
    )
    val_res = DeploymentValidator.validate_deployment(dep)
    assert val_res.is_valid is False
    assert "name must be at least 3 characters" in val_res.errors[0]

    # 2. Duplicate ports
    cfg_dup = DeploymentConfiguration(ports=[80, 80])
    dep_dup = Deployment(
        deployment_id="dep-003",
        name="web-server",
        target=DeploymentTarget.KUBERNETES,
        config=cfg_dup,
        env=env,
    )
    val_dup = DeploymentValidator.validate_deployment(dep_dup)
    assert val_dup.is_valid is False
    assert "Duplicate ports detected" in val_dup.errors[0]


def test_rollback_and_health_abstractions() -> None:
    health = DeploymentHealth(
        status="HEALTHY",
        message="All nodes are healthy",
        timestamp=time.time(),
        checks_performed=["cpu_limit_check", "port_check"],
    )
    assert health.status == "HEALTHY"
    assert "port_check" in health.checks_performed

    meta = RollbackMetadata(
        reason="Manual revert due to memory leak",
        triggered_by="operator-1",
    )
    req = RollbackRequest(
        deployment_id="dep-001",
        target_revision_id=42,
        policy=RollbackPolicy.MANUAL,
        metadata=meta,
    )
    assert req.target_revision_id == 42
    assert req.policy == RollbackPolicy.MANUAL
    assert req.metadata.triggered_by == "operator-1"
