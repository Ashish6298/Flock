"""Unit tests for DeploymentRegistry."""

import time
import pytest
from flock.deployment.exceptions import DeploymentNotFoundError
from flock.deployment.models import DeploymentDefinition, DeploymentRevision
from flock.deployment.registry import DeploymentRegistry


def test_registry_add_and_list() -> None:
    registry = DeploymentRegistry()
    dep = DeploymentDefinition(
        deployment_id="dep-1",
        name="web-server",
        image="nginx:latest",
    )

    registry.register_deployment(dep)
    assert registry.get_deployment("dep-1") == dep

    # Retrieve revisions throws if deployment ID is invalid
    with pytest.raises(DeploymentNotFoundError):
        registry.get_revisions("invalid-dep")

    rev = DeploymentRevision(
        revision_id=1,
        deployment_id="dep-1",
        manifest={"image": "nginx:latest"},
        created_at=time.time(),
    )
    registry.add_revision(rev)
    assert registry.get_revisions("dep-1") == [rev]
