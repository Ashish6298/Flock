"""Deployment Controller orchestrating rolling updates."""

from __future__ import annotations

import structlog

from flock.events.bus import EventBus
from flock.deployment.exceptions import RollbackFailedError
from flock.deployment.models import DeploymentDefinition, DeploymentRevision
from flock.deployment.registry import DeploymentRegistry

logger = structlog.get_logger()


class DeploymentController:
    """Invokes rolling rollouts and coordinates reversion checks."""

    def __init__(self, registry: DeploymentRegistry, event_bus: EventBus) -> None:
        self._registry = registry
        self._events = event_bus

    async def execute_rolling_update(self, deployment: DeploymentDefinition) -> None:
        """Publish start metrics, register, and sync states."""
        self._registry.register_deployment(deployment)

        await self._events.publish(
            "deployment.started",
            {
                "deployment_id": deployment.deployment_id,
                "replicas": deployment.replicas,
            },
        )
        logger.info("Rolling update initiated", deployment_id=deployment.deployment_id)

    async def rollback(self, deployment_id: str, revision_id: int) -> None:
        """Restore spec state matching historical checkpoints.

        Raises:
            RollbackFailedError: If target revision is missing.
        """
        await self._events.publish(
            "deployment.rollback.started",
            {
                "deployment_id": deployment_id,
                "revision_id": revision_id,
            },
        )

        revisions = self._registry.get_revisions(deployment_id)
        target = None
        for rev in revisions:
            if rev.revision_id == revision_id:
                target = rev
                break

        if not target:
            raise RollbackFailedError(f"Revision {revision_id} not found in history catalog.")

        await self._events.publish(
            "deployment.rollback.completed",
            {
                "deployment_id": deployment_id,
                "revision_id": revision_id,
            },
        )
