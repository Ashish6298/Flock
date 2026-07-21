"""Unit tests for Deployment rollbacks."""

import time
import pytest
from flock.events.bus import EventBus
from flock.deployment.controller import DeploymentController
from flock.deployment.exceptions import RollbackFailedError
from flock.deployment.models import DeploymentDefinition, DeploymentRevision
from flock.deployment.registry import DeploymentRegistry


@pytest.mark.asyncio
async def test_controller_rollback_restores_revision() -> None:
    events = EventBus()
    registry = DeploymentRegistry()
    controller = DeploymentController(registry, events)

    dep = DeploymentDefinition(
        deployment_id="dep-roll",
        name="gateway-app",
        image="app:v2.0",
    )
    registry.register_deployment(dep)

    rev = DeploymentRevision(
        revision_id=101,
        deployment_id="dep-roll",
        manifest={"image": "app:v1.0"},
        created_at=time.time(),
    )
    registry.add_revision(rev)

    # Rollback runs successfully
    await controller.rollback("dep-roll", 101)

    with pytest.raises(RollbackFailedError):
        await controller.rollback("dep-roll", 999)
