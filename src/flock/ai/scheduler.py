"""Predictive Scheduler recommending optimal task placements."""

from __future__ import annotations

from typing import Dict, List

from flock.ai.exceptions import OptimizationError


class PredictiveScheduler:
    """Predicts optimal host nodes matching loads constraints."""

    def __init__(self) -> None:
        pass

    def recommend_node(self, node_cpu_loads: Dict[str, float]) -> str:
        """Select least loaded node identifier.

        Raises:
            OptimizationError: If nodes capacity maps are empty.
        """
        if not node_cpu_loads:
            raise OptimizationError("Nodes capacity load mapping cannot be empty.")

        # Heuristic: Select node with lowest CPU load value
        best_node = min(node_cpu_loads, key=node_cpu_loads.get)  # type: ignore
        return str(best_node)
