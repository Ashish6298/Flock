"""Unit tests for cluster rebalancing decisions."""

from flock.orchestrator.models import ClusterSnapshot
from flock.orchestrator.optimizer import OptimizationEngine


def test_rebalancing_skips_balanced_clusters() -> None:
    optimizer = OptimizationEngine(balance_threshold=50.0)
    
    snapshot = ClusterSnapshot(
        timestamp=0.0,
        active_nodes=["node-1", "node-2"],
        task_count=1,
        avg_utilization=10.0,
    )

    plan = optimizer.calculate_rebalance(snapshot)
    assert plan is None
