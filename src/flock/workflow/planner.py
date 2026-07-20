"""Workflow Planner mapping tasks to optimized plans."""

from __future__ import annotations

from typing import List

from flock.workflow.graph import WorkflowGraphEngine
from flock.workflow.models import WorkflowDefinition


class WorkflowPlanner:
    """Converts verified workflow definitions into sequential execution lists."""

    def __init__(self, graph_engine: WorkflowGraphEngine) -> None:
        self._graph = graph_engine

    def build_execution_steps(self, definition: WorkflowDefinition) -> List[str]:
        """Convert DAG into ordered task execution steps."""
        return self._graph.validate_dag(definition)
