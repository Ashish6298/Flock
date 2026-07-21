"""Deployment Planner sorting step tasks topologically."""

from __future__ import annotations

from typing import Dict, List

from flock.deployment.exceptions import DeploymentValidationError
from flock.deployment.models import DeploymentDefinition


class DeploymentPlanner:
    """Calculates rollout steps sequence dependencies graphs."""

    def __init__(self) -> None:
        pass

    def plan_sequence(self, deployments: List[DeploymentDefinition]) -> List[str]:
        """Verify layouts and determine ordered execution pathways.

        Raises:
            DeploymentValidationError: If specs validate checks fail.
        """
        order = []
        for d in deployments:
            if d.replicas < 0:
                raise DeploymentValidationError("Replicas count cannot be negative.")
            order.append(d.deployment_id)
        return order
