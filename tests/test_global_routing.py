"""Unit tests for GlobalRoutingEngine."""

import pytest
from flock.federation.exceptions import FederationRoutingError
from flock.federation.models import FederationCluster
from flock.federation.routing import GlobalRoutingEngine


def test_routing_engine_picks_highest_capacity() -> None:
    engine = GlobalRoutingEngine()

    c1 = FederationCluster(cluster_id="c1", name="west", endpoints=[], is_healthy=True, capacity_score=10.0)
    c2 = FederationCluster(cluster_id="c2", name="east", endpoints=[], is_healthy=True, capacity_score=20.0)

    # Picks c2 because 20.0 > 10.0
    dec = engine.route_task("task-1", "c1", [c1, c2])
    assert dec.destination_cluster == "c2"


def test_routing_empty_candidates_raises() -> None:
    engine = GlobalRoutingEngine()
    with pytest.raises(FederationRoutingError):
        engine.route_task("task-1", "c1", [])
