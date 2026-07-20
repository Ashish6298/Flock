"""Scheduling Engine executing task dispatches under leader ownership."""

from __future__ import annotations

import asyncio
from typing import Optional

import structlog

from flock.events.bus import EventBus
from flock.scheduling.models import ScheduleDefinition, ScheduleExecution

logger = structlog.get_logger()


class SchedulingEngine:
    """Coordinating scheduling ticks and leader checkpoints."""

    def __init__(self, event_bus: EventBus) -> None:
        self._events = event_bus
        self.is_leader = False

    def acquire_leadership(self) -> None:
        """Mark this node as scheduler leader."""
        self.is_leader = True

    def revoke_leadership(self) -> None:
        """Step down this node scheduler leadership."""
        self.is_leader = False

    async def execute_schedule(self, schedule: ScheduleDefinition, execution: ScheduleExecution) -> bool:
        """Fire scheduled execution event if leader.

        Returns:
            bool status indicating execution acceptance.
        """
        if not self.is_leader:
            logger.debug("Skipping scheduled run: Node is not the scheduler leader.")
            return False

        logger.info(
            "Executing scheduled task",
            schedule_id=schedule.schedule_id,
            execution_id=execution.execution_id,
        )

        # Notify EventBus execution started
        await self._events.publish(
            "schedule.execution.started",
            {
                "schedule_id": schedule.schedule_id,
                "execution_id": execution.execution_id,
            },
        )

        await asyncio.sleep(0.01)

        await self._events.publish(
            "schedule.execution.completed",
            {
                "schedule_id": schedule.schedule_id,
                "execution_id": execution.execution_id,
            },
        )

        return True
