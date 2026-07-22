"""Telemetry metrics updates and health checks reporting for recovery operations."""

from __future__ import annotations

import threading
from typing import Optional
from flock.recovery.models import RecoveryMetricsReport


class RecoveryMetricsTracker:
    """Tracks and generates reports on recovery performance and health status."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._snapshots_taken = 0
        self._backups_created = 0
        self._restores_executed = 0
        self._last_backup_time: Optional[float] = None
        self._last_restore_time: Optional[float] = None
        self._health_status = "HEALTHY"

    def record_snapshot(self) -> None:
        with self._lock:
            self._snapshots_taken += 1

    def record_backup(self, timestamp: float) -> None:
        with self._lock:
            self._backups_created += 1
            self._last_backup_time = timestamp

    def record_restore(self, timestamp: float) -> None:
        with self._lock:
            self._restores_executed += 1
            self._last_restore_time = timestamp

    def set_health_status(self, status: str) -> None:
        with self._lock:
            self._health_status = status

    def generate_report(self) -> RecoveryMetricsReport:
        """Produce a strongly typed metrics report snapshot."""
        with self._lock:
            return RecoveryMetricsReport(
                total_snapshots_taken=self._snapshots_taken,
                total_backups_created=self._backups_created,
                total_restores_executed=self._restores_executed,
                last_backup_timestamp=self._last_backup_time,
                last_restore_timestamp=self._last_restore_time,
                health_status=self._health_status,
            )
