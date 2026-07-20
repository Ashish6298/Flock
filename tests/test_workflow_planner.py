"""Unit tests for WorkflowPlanner."""

from flock.workflow.graph import WorkflowGraphEngine
from flock.workflow.models import WorkflowDefinition, WorkflowEdge, WorkflowNode
from flock.workflow.planner import WorkflowPlanner


def test_planner_topological_sort() -> None:
    graph = WorkflowGraphEngine()
    planner = WorkflowPlanner(graph)

    n1 = WorkflowNode(node_id="n1", task_payload=b"")
    n2 = WorkflowNode(node_id="n2", task_payload=b"")
    e1 = WorkflowEdge(source_id="n1", target_id="n2")

    definition = WorkflowDefinition(
        workflow_id="wf-1",
        nodes=[n1, n2],
        edges=[e1],
    )

    steps = planner.build_execution_steps(definition)
    assert steps == ["n1", "n2"]
