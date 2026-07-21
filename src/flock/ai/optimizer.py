"""Autonomous Optimization Engine."""

from __future__ import annotations

from typing import Dict, List

from flock.ai.models import OptimizationPlan


class AutonomousOptimizationEngine:
    """Evaluates cluster telemetries and generates tuning commands."""

    def __init__(self) -> None:
        pass

    def generate_plan(self, metrics: Dict[str, float]) -> OptimizationPlan:
        """Create tuning actions based on metrics values."""
        actions: List[str] = []
        
        cpu_load = metrics.get("cpu_load", 0.0)
        if cpu_load > 0.8:
            actions.append("SCALE_UP_REPLICAS")
            actions.append("MIGRATE_HEAVY_TASKS")

        memory_load = metrics.get("memory_load", 0.0)
        if memory_load > 0.85:
            actions.append("PURGE_EXPIRED_CACHES")

        return OptimizationPlan(actions=actions)
