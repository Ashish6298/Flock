"""Workflow Graph Engine validating DAG cycles and topological sorting."""

from __future__ import annotations

from collections import deque
from typing import Dict, List, Set

from flock.workflow.exceptions import CircularDependencyError, WorkflowValidationError
from flock.workflow.models import WorkflowDefinition


class WorkflowGraphEngine:
    """Validates structural properties of Workflow definitions."""

    def __init__(self) -> None:
        pass

    def validate_dag(self, definition: WorkflowDefinition) -> List[str]:
        """Validate workflow edges contain no circular loops.

        Returns:
            List[str] representing resolved topological execution order.

        Raises:
            CircularDependencyError: If a loop is detected.
            WorkflowValidationError: If nodes are missing or edges reference invalid IDs.
        """
        # Initialize graph structures
        nodes = {n.node_id for n in definition.nodes}
        adj: Dict[str, List[str]] = {n: [] for n in nodes}
        in_degree: Dict[str, int] = {n: 0 for n in nodes}

        # Build adjacency and in-degree limits
        for edge in definition.edges:
            if edge.source_id not in nodes or edge.target_id not in nodes:
                raise WorkflowValidationError(f"Edge links missing node IDs: '{edge.source_id}' -> '{edge.target_id}'.")
            adj[edge.source_id].append(edge.target_id)
            in_degree[edge.target_id] += 1

        # Kahn's algorithm for topological sorting
        queue = deque([n for n in nodes if in_degree[n] == 0])
        ordered: List[str] = []

        while queue:
            curr = queue.popleft()
            ordered.append(curr)
            for neighbor in adj[curr]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        if len(ordered) != len(nodes):
            raise CircularDependencyError("Workflow contains a circular dependency loop.")

        return ordered
