"""Telemetry statistics aggregation and failover indicators tracking."""

from __future__ import annotations

import time
import threading
from typing import Optional
from flock.federation.models import FederationMetricsReport


class FederationMetricsTracker:
    """Tracks performance and failover telemetry indices across federated link points."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._remote_executions = 0
        self._failover_successes = 0
        self._replication_delay = 0.0

    def record_remote_execution(self) -> None:
        with self._lock:
            self._remote_executions += 1

    def record_failover(self, success: bool) -> None:
        with self._lock:
            if success:
                self._failover_successes += 1

    def update_replication_delay(self, delay_seconds: float) -> None:
        with self._lock:
            self._replication_delay = delay_seconds

    def generate_report(self, active_clusters_count: int) -> FederationMetricsReport:
        """Produce a strongly typed metrics report summary."""
        with self._lock:
            return FederationMetricsReport(
                timestamp=time.time(),
                active_clusters_count=active_clusters_count,
                remote_executions_count=self._remote_executions,
                replication_delay_seconds=self._replication_delay,
                failover_success_count=self._failover_successes,
            )
