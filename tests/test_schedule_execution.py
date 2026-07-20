"""Unit tests for scheduled execution lifecycle events."""

import asyncio
from typing import Dict, Any
import pytest
from flock.events.bus import EventBus
from flock.scheduling.models import ScheduleDefinition, ScheduleExecution
from flock.scheduling.scheduler import SchedulingEngine


@pytest.mark.asyncio
async def test_schedule_execution_events() -> None:
    events = EventBus()
    engine = SchedulingEngine(events)
    engine.acquire_leadership()

    completions = []

    async def on_completion(data: Dict[str, Any]) -> None:
        completions.append(data)

    events.subscribe("schedule.execution.completed", on_completion)

    sch = ScheduleDefinition(schedule_id="sch-3", cron_expression="*", task_payload=b"")
    exec_run = ScheduleExecution(execution_id="run-12", schedule_id="sch-3", triggered_at=0.0, status="PENDING")

    await engine.execute_schedule(sch, exec_run)
    await asyncio.sleep(0.01)

    assert len(completions) == 1
    assert completions[0]["schedule_id"] == "sch-3"
