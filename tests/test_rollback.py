"""Unit tests for RollbackEngine, DeploymentRegistry, and Verifier."""

import time
import pytest
from flock.deployment.exceptions import RollbackFailedError
from flock.deployment.models import (
    DeploymentDefinition,
    DeploymentRevision,
    RollbackRequest,
    RollbackMetadata,
    RollbackPolicy,
)
from flock.deployment.registry import DeploymentRegistry
from flock.deployment.rollback import RollbackEngine, DeploymentVerifier


def test_registry_revision_pruning_and_lookups() -> None:
    registry = DeploymentRegistry()
    dep = DeploymentDefinition(
        deployment_id="dep-1",
        name="web-service",
        image="nginx:latest",
    )
    registry.register_deployment(dep)

    # 1. Add revisions
    rev1 = DeploymentRevision(revision_id=1, deployment_id="dep-1", manifest={"file": "1"}, created_at=time.time())
    rev2 = DeploymentRevision(revision_id=2, deployment_id="dep-1", manifest={"file": "2"}, created_at=time.time())
    rev3 = DeploymentRevision(revision_id=3, deployment_id="dep-1", manifest={"file": "3"}, created_at=time.time())
    registry.add_revision(rev1)
    registry.add_revision(rev2)
    registry.add_revision(rev3)

    # 2. Verify lookups
    assert registry.get_latest_revision("dep-1").revision_id == 3
    assert registry.get_previous_stable_revision("dep-1").revision_id == 2

    # 3. Pruning
    pruned = registry.prune_revisions("dep-1", limit=2)
    assert pruned == 1
    assert len(registry.get_revisions("dep-1")) == 2
    assert registry.get_latest_revision("dep-1").revision_id == 3
    assert registry.get_previous_stable_revision("dep-1").revision_id == 2


def test_rollback_engine_success_and_failure() -> None:
    registry = DeploymentRegistry()
    dep = DeploymentDefinition(
        deployment_id="dep-2",
        name="api-service",
        image="nginx:latest",
    )
    registry.register_deployment(dep)

    rev1 = DeploymentRevision(revision_id=1, deployment_id="dep-2", manifest={"file": "1"}, created_at=time.time())
    rev2 = DeploymentRevision(revision_id=2, deployment_id="dep-2", manifest={"file": "2"}, created_at=time.time())
    registry.add_revision(rev1)
    registry.add_revision(rev2)

    engine = RollbackEngine(registry)
    meta = RollbackMetadata(reason="Deploy error")
    req = RollbackRequest(
        deployment_id="dep-2",
        target_revision_id=1,
        policy=RollbackPolicy.IMMEDIATE,
        metadata=meta,
    )

    # Validate & Execute rollback
    val_res = engine.validate_rollback_request(req)
    assert val_res.is_valid is True

    result = engine.execute_rollback(req)
    assert result.success is True
    assert result.previous_revision_id == 2
    assert result.restored_revision_id == 1

    # Verify new revision is added representing rollback target
    latest = registry.get_latest_revision("dep-2")
    assert latest.revision_id == 3
    assert latest.manifest == {"file": "1"}

    # Mismatched target revision ID failure
    invalid_req = RollbackRequest(
        deployment_id="dep-2",
        target_revision_id=99,
        policy=RollbackPolicy.IMMEDIATE,
        metadata=meta,
    )
    with pytest.raises(RollbackFailedError):
        engine.execute_rollback(invalid_req)


def test_deployment_verifier() -> None:
    registry = DeploymentRegistry()
    verifier = DeploymentVerifier(registry)

    # Missing deployment
    res = verifier.verify_release("rel-1", "missing-id")
    assert res.is_healthy is False
    assert any("does not exist" in err for err in res.errors)
