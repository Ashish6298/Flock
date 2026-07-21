"""Unit tests for DeploymentPlanner."""

import pytest
from flock.deployment.exceptions import DeploymentValidationError
from flock.deployment.models import DeploymentDefinition
from flock.deployment.planner import DeploymentPlanner


def test_planner_sorts_topological_deployments() -> None:
    planner = DeploymentPlanner()
    dep1 = DeploymentDefinition(deployment_id="d1", name="service-a", image="image-a")
    dep2 = DeploymentDefinition(deployment_id="d2", name="service-b", image="image-b")

    order = planner.plan_sequence([dep1, dep2])
    assert order == ["d1", "d2"]


def test_planner_negative_replicas_raises() -> None:
    planner = DeploymentPlanner()
    dep_invalid = DeploymentDefinition(deployment_id="d1", name="service-a", image="image-a", replicas=-5)

    with pytest.raises(DeploymentValidationError):
        planner.plan_sequence([dep_invalid])
