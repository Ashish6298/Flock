"""Unit tests for LoadBalancingEngine."""

from flock.resources.loadbalancer import (
    LeastUtilizedStrategy,
    LoadBalancingEngine,
    RoundRobinStrategy,
)
from flock.resources.models import NodeResourceProfile


def test_least_utilized_heuristics() -> None:
    engine = LoadBalancingEngine(LeastUtilizedStrategy())

    n1 = NodeResourceProfile(node_id="n1", cpu_cores=8, cpu_util=80.0, memory_mb=100, memory_util=10)
    n2 = NodeResourceProfile(node_id="n2", cpu_cores=8, cpu_util=10.0, memory_mb=100, memory_util=10)

    # Lowest CPU loaded node chosen
    choice = engine.select_candidate([n1, n2])
    assert choice == "n2"


def test_round_robin_heuristics() -> None:
    engine = LoadBalancingEngine(RoundRobinStrategy())

    n1 = NodeResourceProfile(node_id="n1", cpu_cores=8, cpu_util=10.0, memory_mb=100, memory_util=10)
    n2 = NodeResourceProfile(node_id="n2", cpu_cores=8, cpu_util=10.0, memory_mb=100, memory_util=10)

    choice1 = engine.select_candidate([n1, n2])
    choice2 = engine.select_candidate([n1, n2])
    
    assert choice1 != choice2
