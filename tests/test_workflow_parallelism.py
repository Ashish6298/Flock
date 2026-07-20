"""Unit tests for workflow parallel execution patterns."""

import pytest
from flock.workflow.graph import WorkflowGraphEngine
from flock.workflow.models import WorkflowDefinition, WorkflowEdge, WorkflowNode


def test_parallel_independent_steps() -> None:
    engine = WorkflowGraphEngine()

    n1 = WorkflowNode(node_id="n1", task_payload=b"")
    n2 = WorkflowNode(node_id="n2", task_payload=b"")
    
    # n1 and n2 are independent (parallel branches)
    definition = WorkflowDefinition(
        workflow_id="wf-parallel",
        nodes=[n1, n2],
        edges=[],
    )

    order = engine.validate_dag(definition)
    # Both nodes are in the topological list (order doesn't matter since they are independent)
    assert "n1" in order
    assert "n2" in order
    assert len(order) == 2
