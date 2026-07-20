"""Unit tests for SchedulingEngine leader logic."""

import pytest
from flock.events.bus import EventBus
from flock.scheduling.models import ScheduleDefinition, ScheduleExecution
from flock.scheduling.scheduler import SchedulingEngine


@pytest.mark.asyncio
async def test_scheduler_leadership_execution() -> None:
    events = EventBus()
    engine = SchedulingEngine(events)

    sch = ScheduleDefinition(schedule_id="sch-2", cron_expression="*", task_payload=b"")
    exec_run = ScheduleExecution(execution_id="run-1", schedule_id="sch-2", triggered_at=0.0, status="PENDING")

    # Non-leader skips execution
    assert await engine.execute_schedule(sch, exec_run) is False

    # Leader accepts execution
    engine.acquire_leadership()
    assert await engine.execute_schedule(sch, exec_run) is True
