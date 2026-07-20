"""Unit tests for ScheduleRegistry."""

import pytest
from flock.scheduling.exceptions import DuplicateScheduleError
from flock.scheduling.models import ScheduleDefinition
from flock.scheduling.registry import ScheduleRegistry


def test_registry_add_and_list() -> None:
    registry = ScheduleRegistry()
    sch = ScheduleDefinition(
        schedule_id="sch-1",
        cron_expression="*/5 * * * *",
        task_payload=b"",
    )

    registry.add_schedule(sch)
    assert registry.get_schedule("sch-1") == sch
    assert len(registry.list_schedules()) == 1

    # Duplicate add throws error
    with pytest.raises(DuplicateScheduleError):
        registry.add_schedule(sch)

    registry.remove_schedule("sch-1")
    assert registry.get_schedule("sch-1") is None
