"""Unit tests for DeploymentController."""

import pytest
from flock.events.bus import EventBus
from flock.deployment.controller import DeploymentController
from flock.deployment.models import DeploymentDefinition
from flock.deployment.registry import DeploymentRegistry


@pytest.mark.asyncio
async def test_controller_executes_rolling_update() -> None:
    events = EventBus()
    registry = DeploymentRegistry()
    controller = DeploymentController(registry, events)

    dep = DeploymentDefinition(
        deployment_id="dep-controller",
        name="gateway-app",
        image="app:v1.0",
    )

    await controller.execute_rolling_update(dep)
    assert registry.get_deployment("dep-controller") == dep
