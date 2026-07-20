"""Unit tests for WorkflowGraphEngine DAG validations."""

import pytest
from flock.workflow.exceptions import CircularDependencyError, WorkflowValidationError
from flock.workflow.graph import WorkflowGraphEngine
from flock.workflow.models import WorkflowDefinition, WorkflowEdge, WorkflowNode


def test_graph_validation_detects_cycles() -> None:
    engine = WorkflowGraphEngine()

    n1 = WorkflowNode(node_id="n1", task_payload=b"")
    n2 = WorkflowNode(node_id="n2", task_payload=b"")

    # Circular loop
    e1 = WorkflowEdge(source_id="n1", target_id="n2")
    e2 = WorkflowEdge(source_id="n2", target_id="n1")

    definition = WorkflowDefinition(
        workflow_id="wf-1",
        nodes=[n1, n2],
        edges=[e1, e2],
    )

    with pytest.raises(CircularDependencyError):
        engine.validate_dag(definition)


def test_topological_ordering() -> None:
    engine = WorkflowGraphEngine()

    n1 = WorkflowNode(node_id="n1", task_payload=b"")
    n2 = WorkflowNode(node_id="n2", task_payload=b"")
    e1 = WorkflowEdge(source_id="n1", target_id="n2")

    definition = WorkflowDefinition(
        workflow_id="wf-1",
        nodes=[n1, n2],
        edges=[e1],
    )

    order = engine.validate_dag(definition)
    assert order == ["n1", "n2"]
