"""Unit tests for federation failovers."""

from flock.federation.models import FederationCluster
from flock.federation.routing import GlobalRoutingEngine


def test_routing_skips_unhealthy_clusters() -> None:
    engine = GlobalRoutingEngine()

    # c2 has high score but is unhealthy
    c1 = FederationCluster(cluster_id="c1", name="west", endpoints=[], is_healthy=True, capacity_score=10.0)
    c2 = FederationCluster(cluster_id="c2", name="east", endpoints=[], is_healthy=False, capacity_score=99.0)

    dec = engine.route_task("task-1", "c1", [c1, c2])
    assert dec.destination_cluster == "c1"
