"""Unit tests for WorkflowExecutor."""

import pytest
from unittest.mock import MagicMock
from flock.events.bus import EventBus
from flock.workflow.checkpoint import WorkflowCheckpointManager
from flock.workflow.executor import WorkflowExecutor
from flock.workflow.models import WorkflowDefinition, WorkflowNode


@pytest.mark.asyncio
async def test_executor_runs_topological_steps() -> None:
    events = EventBus()
    checkpoints = MagicMock(spec=WorkflowCheckpointManager)
    executor = WorkflowExecutor(events, checkpoints)

    definition = WorkflowDefinition(
        workflow_id="wf-1",
        nodes=[WorkflowNode(node_id="n1", task_payload=b"")],
        edges=[],
    )

    res = await executor.execute("inst-1", definition, ["n1"])
    assert res.success is True
    assert checkpoints.save_checkpoint.call_count == 1
