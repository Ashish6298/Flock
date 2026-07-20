"""Telemetry Aggregator."""

from __future__ import annotations

import time
from typing import Any, Dict, List

import structlog

from flock.events.bus import EventBus
from flock.observability.models import MetricType
from flock.observability.registry import MetricsRegistry

logger = structlog.get_logger()


class TelemetryAggregator:
    """Consumes EventBus instrumentation signals to construct aggregate statistics."""

    def __init__(self, registry: MetricsRegistry, event_bus: EventBus) -> None:
        self._registry = registry
        self._events = event_bus
        self._is_subscribed = False

    def start(self) -> None:
        """Register local EventBus metric-updating callbacks."""
        if self._is_subscribed:
            return
        
        # Wire hooks for consensus, FSM, scheduling, placement, worker events
        self._events.subscribe("consensus.log.committed", self._on_raft_commit)
        self._events.subscribe("state.command.applied", self._on_fsm_command)
        self._events.subscribe("task.scheduled", self._on_task_scheduled)
        self._events.subscribe("task.execution.started", self._on_task_execution_started)
        
        self._is_subscribed = True

    async def _on_raft_commit(self, event_data: Dict[str, Any]) -> None:
        """Increment count of consensus commit events."""
        self._registry.increment("flock.consensus.commits.total")
        term = event_data.get("term", 0.0)
        self._registry.set_gauge("flock.consensus.current_term", float(term))

    async def _on_fsm_command(self, event_data: Dict[str, Any]) -> None:
        """Increment count of executed FSM state mutations."""
        self._registry.increment("flock.fsm.commands.total")

    async def _on_task_scheduled(self, event_data: Dict[str, Any]) -> None:
        """Increment count of tasks registered inside scheduler."""
        self._registry.increment("flock.scheduler.tasks.total")

    async def _on_task_execution_started(self, event_data: Dict[str, Any]) -> None:
        """Increment count of worker runtime execution starts."""
        self._registry.increment("flock.worker.executions.total")
