"""Unit tests for task migration boundaries."""

import pytest
from flock.events.bus import EventBus
from flock.orchestrator.models import MigrationPlan
from flock.orchestrator.scheduler import AutonomousScheduler


@pytest.mark.asyncio
async def test_migration_precheck_enforcement() -> None:
    events = EventBus()
    scheduler = AutonomousScheduler(events)

    plan = MigrationPlan(
        task_id="task-12",
        source_node="n1",
        target_node="n2",
        pre_check_passed=True,
    )

    assert await scheduler.execute_migration(plan) is True
