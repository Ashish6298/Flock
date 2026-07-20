"""Schedule Registry storing active schedules."""

from __future__ import annotations

import threading
from typing import Dict, List, Optional

from flock.scheduling.exceptions import DuplicateScheduleError
from flock.scheduling.models import ScheduleDefinition


class ScheduleRegistry:
    """Thread-safe catalog directory tracking schedule blueprints."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._schedules: Dict[str, ScheduleDefinition] = {}

    def add_schedule(self, schedule: ScheduleDefinition) -> None:
        """Register schedule definition parameters.

        Raises:
            DuplicateScheduleError: If schedule ID is already registered.
        """
        with self._lock:
            if schedule.schedule_id in self._schedules:
                raise DuplicateScheduleError(f"Schedule '{schedule.schedule_id}' already registered.")
            self._schedules[schedule.schedule_id] = schedule

    def get_schedule(self, schedule_id: str) -> Optional[ScheduleDefinition]:
        """Fetch schedule definition settings."""
        with self._lock:
            return self._schedules.get(schedule_id)

    def remove_schedule(self, schedule_id: str) -> None:
        """Remove schedule from registry."""
        with self._lock:
            self._schedules.pop(schedule_id, None)

    def list_schedules(self) -> List[ScheduleDefinition]:
        """List all active and inactive schedules."""
        with self._lock:
            return list(self._schedules.values())
