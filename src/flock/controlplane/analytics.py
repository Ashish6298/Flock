"""Control plane analytics aggregates engine."""

from __future__ import annotations

import time
import threading
from flock.controlplane.models import FleetMetricsReport


class FleetAnalyticsEngine:
    """Aggregates metrics trackers and reports fleet-wide performance summaries."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._total_clusters = 0
        self._active_clusters = 0
        self._compliance_score = 100.0
        self._upgrade_progress = 0.0

    def update_metrics(
        self,
        total: int,
        active: int,
        compliance: float,
        upgrade: float,
    ) -> None:
        with self._lock:
            self._total_clusters = total
            self._active_clusters = active
            self._compliance_score = compliance
            self._upgrade_progress = upgrade

    def generate_report(self) -> FleetMetricsReport:
        """Produce a strongly typed metrics report snapshot."""
        with self._lock:
            return FleetMetricsReport(
                timestamp=time.time(),
                total_clusters=self._total_clusters,
                active_clusters=self._active_clusters,
                compliance_score=self._compliance_score,
                upgrade_progress=self._upgrade_progress,
            )
