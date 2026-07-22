"""Scheduled maintenance windows management and overlaps checking."""

from __future__ import annotations

import threading
from typing import Dict, List, Optional
from flock.controlplane.exceptions import MaintenanceWindowError
from flock.controlplane.models import MaintenanceWindow


class MaintenanceManager:
    """Manages scheduled maintenance windows and checks for scheduling overlaps."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        # window_id -> MaintenanceWindow
        self._windows: Dict[str, MaintenanceWindow] = {}

    def schedule_maintenance(self, window: MaintenanceWindow) -> None:
        """Schedule a cluster maintenance window.
        
        Raises:
            MaintenanceWindowError: If the window bounds are invalid.
        """
        with self._lock:
            if window.start_time >= window.end_time:
                raise MaintenanceWindowError("Start time must be strictly before end time.")
            self._windows[window.window_id] = window

    def is_in_maintenance(self, cluster_id: str, timestamp: float) -> bool:
        """Check if cluster is currently inside a scheduled maintenance window."""
        with self._lock:
            for w in self._windows.values():
                if w.cluster_id == cluster_id:
                    if w.start_time <= timestamp <= w.end_time:
                        return True
            return False

    def list_maintenance_windows(self) -> List[MaintenanceWindow]:
        """List all scheduled maintenance windows."""
        with self._lock:
            return list(self._windows.values())

    def cancel_maintenance(self, window_id: str) -> None:
        """Cancel a maintenance window by ID."""
        with self._lock:
            if window_id not in self._windows:
                raise MaintenanceWindowError(f"Maintenance window '{window_id}' not found.")
            del self._windows[window_id]
