"""Unit tests for ResourceBalancer."""

from flock.resources.balancer import ResourceBalancer
from flock.resources.models import NodeResourceProfile


def test_balancer_skew_evaluation() -> None:
    balancer = ResourceBalancer(imbalance_threshold=20.0)

    # Imbalanced nodes
    n1 = NodeResourceProfile(node_id="n1", cpu_cores=8, cpu_util=90.0, memory_mb=100, memory_util=10)
    n2 = NodeResourceProfile(node_id="n2", cpu_cores=8, cpu_util=10.0, memory_mb=100, memory_util=10)

    decision = balancer.evaluate_skew([n1, n2])
    assert decision is not None
    assert decision.source_node == "n1"
    assert decision.target_node == "n2"
    assert decision.task_id == "auto-migrated-task-0"
