"""Unit tests for AutonomousScheduler."""

import asyncio
from typing import Dict, Any
import pytest
from flock.events.bus import EventBus
from flock.orchestrator.exceptions import MigrationRejectedError
from flock.orchestrator.models import MigrationPlan
from flock.orchestrator.scheduler import AutonomousScheduler


@pytest.mark.asyncio
async def test_migration_lifecycle_events() -> None:
    events = EventBus()
    scheduler = AutonomousScheduler(events)

    migrations = []

    async def on_migration_start(data: Dict[str, Any]) -> None:
        migrations.append(data)

    events.subscribe("task.migration.started", on_migration_start)

    plan = MigrationPlan(
        task_id="task-10",
        source_node="node-1",
        target_node="node-2",
        pre_check_passed=True,
    )

    success = await scheduler.execute_migration(plan)
    assert success is True

    # Let event loop run tasks
    await asyncio.sleep(0.01)

    assert len(migrations) == 1
    assert migrations[0]["task_id"] == "task-10"


@pytest.mark.asyncio
async def test_rejected_migration_raises() -> None:
    events = EventBus()
    scheduler = AutonomousScheduler(events)

    plan = MigrationPlan(
        task_id="task-10",
        source_node="node-1",
        target_node="node-2",
        pre_check_passed=False,
    )

    with pytest.raises(MigrationRejectedError):
        await scheduler.execute_migration(plan)
