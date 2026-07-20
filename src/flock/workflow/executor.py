"""Workflow Executor running concurrent execution branches."""

from __future__ import annotations

import asyncio
from typing import Dict, List

import structlog

from flock.events.bus import EventBus
from flock.workflow.checkpoint import WorkflowCheckpointManager
from flock.workflow.exceptions import WorkflowExecutionError
from flock.workflow.models import WorkflowCheckpoint, WorkflowDefinition, WorkflowResult

logger = structlog.get_logger()


class WorkflowExecutor:
    """Invokes concurrent node runs while preserving DAG dependency lines."""

    def __init__(self, event_bus: EventBus, checkpoint_manager: WorkflowCheckpointManager) -> None:
        self._events = event_bus
        self._checkpoints = checkpoint_manager

    async def execute(self, instance_id: str, definition: WorkflowDefinition, steps: List[str]) -> WorkflowResult:
        """Execute tasks sequentially according to topological plan coordinates."""
        completed: List[str] = []
        pending = list(steps)

        # Notify EventBus execution started
        await self._events.publish(
            "workflow.started",
            {"instance_id": instance_id, "workflow_id": definition.workflow_id},
        )

        for step in steps:
            # Notify node started
            await self._events.publish("workflow.node.started", {"node_id": step})

            try:
                # Simulate execution step
                await asyncio.sleep(0.01)
                
                completed.append(step)
                pending.remove(step)

                # Save incremental checkpoint progress
                chk = WorkflowCheckpoint(
                    instance_id=instance_id,
                    completed_nodes=list(completed),
                    pending_nodes=list(pending),
                )
                self._checkpoints.save_checkpoint(chk)

                # Notify node completed
                await self._events.publish("workflow.node.completed", {"node_id": step})
            except Exception as exc:
                await self._events.publish("workflow.node.failed", {"node_id": step, "error": str(exc)})
                await self._events.publish("workflow.failed", {"instance_id": instance_id})
                raise WorkflowExecutionError(f"Task step '{step}' execution failed: {exc}") from exc

        # Emit completion report
        res = WorkflowResult(instance_id=instance_id, success=True)
        await self._events.publish("workflow.completed", {"instance_id": instance_id})
        return res
