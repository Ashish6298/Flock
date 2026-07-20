"""Unit tests for GlobalScheduler."""

import asyncio
from typing import Dict, Any
import pytest
from flock.events.bus import EventBus
from flock.federation.exceptions import GlobalSchedulingError
from flock.federation.models import GlobalTask, RoutingDecision
from flock.federation.scheduler import GlobalScheduler


@pytest.mark.asyncio
async def test_global_scheduling_events() -> None:
    events = EventBus()
    scheduler = GlobalScheduler(events)

    assignments = []

    async def on_task_assigned(data: Dict[str, Any]) -> None:
        assignments.append(data)

    events.subscribe("global.task.assigned", on_task_assigned)

    task = GlobalTask(
        task_id="global-1",
        payload=b"bytes",
    )

    decision = RoutingDecision(
        decision_id="dec-1",
        task_id="global-1",
        source_cluster="cluster-a",
        destination_cluster="cluster-b",
    )

    success = await scheduler.schedule_global_task(task, decision)
    assert success is True

    # Let event loop run tasks
    await asyncio.sleep(0.01)

    assert len(assignments) == 1
    assert assignments[0]["task_id"] == "global-1"


@pytest.mark.asyncio
async def test_scheduler_id_mismatch_raises() -> None:
    events = EventBus()
    scheduler = GlobalScheduler(events)

    task = GlobalTask(task_id="task-x", payload=b"")
    decision = RoutingDecision(
        decision_id="dec-1",
        task_id="task-y",  # Mismatch ID
        source_cluster="cluster-a",
        destination_cluster="cluster-b",
    )

    with pytest.raises(GlobalSchedulingError):
        await scheduler.schedule_global_task(task, decision)
