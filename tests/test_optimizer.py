"""Unit tests for OptimizationEngine."""

from flock.orchestrator.models import ClusterSnapshot
from flock.orchestrator.optimizer import OptimizationEngine


def test_optimizer_rebalances_imbalanced_cluster() -> None:
    optimizer = OptimizationEngine(balance_threshold=30.0)

    # Imbalanced snapshot
    snapshot = ClusterSnapshot(
        timestamp=0.0,
        active_nodes=["node-1", "node-2"],
        task_count=10,
        avg_utilization=85.0,
    )

    plan = optimizer.calculate_rebalance(snapshot)
    assert plan is not None
    assert plan.tasks_to_migrate == {"task-x": "node-1"}
