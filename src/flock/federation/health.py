"""Geographical clusters health metrics summaries and availability monitoring."""

from __future__ import annotations

import threading
from typing import Dict
from flock.federation.models import FederationHealth


class FederationHealthMonitor:
    """Aggregates availability states from member clusters and reports combined health metrics."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        # cluster_id -> healthy status (bool)
        self._healths: Dict[str, bool] = {}

    def set_cluster_health(self, cluster_id: str, is_healthy: bool) -> None:
        with self._lock:
            self._healths[cluster_id] = is_healthy

    def get_health_report(self) -> FederationHealth:
        """Produce a combined health metric summary of the federated mesh."""
        with self._lock:
            if not self._healths:
                return FederationHealth(status="HEALTHY", cluster_healths={})
                
            unhealthy_count = sum(1 for val in self._healths.values() if not val)
            
            if unhealthy_count == 0:
                status = "HEALTHY"
            elif unhealthy_count < len(self._healths):
                status = "DEGRADED"
            else:
                status = "UNHEALTHY"
                
            return FederationHealth(
                status=status,
                cluster_healths=dict(self._healths),
            )
