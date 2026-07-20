"""Local Node and Cluster Health Monitoring subsystem."""

from __future__ import annotations

import threading
import time
from typing import Dict

import structlog

from flock.events.bus import EventBus
from flock.observability.models import NodeHealthReport
from flock.observability.registry import MetricsRegistry

logger = structlog.get_logger()


class HealthMonitor:
    """Evaluates node health metrics to produce structured status reports."""

    def __init__(self, node_id: str, registry: MetricsRegistry, event_bus: EventBus) -> None:
        self.node_id = node_id
        self._registry = registry
        self._events = event_bus
        self._lock = threading.Lock()
        self._last_status = "HEALTHY"

    def evaluate_health(self) -> NodeHealthReport:
        """Run liveness evaluations, check values, and generate health reports."""
        with self._lock:
            # 1. Fetch system metrics values
            metrics: Dict[str, float] = {}
            for metric in self._registry.list_metrics():
                metrics[metric.name] = metric.value

            # 2. Evaluate thresholds to determine status flag
            status = "HEALTHY"
            
            # If WAL corruption or storage errors were logged (check local counter if exists)
            wal_errors = metrics.get("flock.storage.wal_corruptions.total", 0.0)
            if wal_errors > 0.0:
                status = "UNHEALTHY"

            # Check for consensus term stability or heartbeat failures if available
            heartbeat_failures = metrics.get("flock.heartbeat.failures.total", 0.0)
            if heartbeat_failures > 5.0:
                status = "DEGRADED"

            # Trigger EventBus lifecycle changes on health transitions
            if status != self._last_status:
                logger.warn(
                    "Node status changed",
                    node_id=self.node_id,
                    old_status=self._last_status,
                    new_status=status,
                )
                self._last_status = status
                
                import asyncio
                try:
                    loop = asyncio.get_running_loop()
                    loop.create_task(
                        self._events.publish(
                            "node.health.changed",
                            {"node_id": self.node_id, "status": status},
                        )
                    )
                except RuntimeError:
                    pass

            return NodeHealthReport(
                node_id=self.node_id,
                status=status,
                metrics=metrics,
                timestamp=time.time(),
            )
