"""Unit tests for TrafficRouter."""

import pytest
from flock.mesh.exceptions import RoutingPolicyError
from flock.mesh.models import ServiceEndpoint
from flock.mesh.router import TrafficRouter


def test_router_weighted_choices() -> None:
    router = TrafficRouter()

    ep1 = ServiceEndpoint(endpoint_id="ep-1", host="127.0.0.1", port=8080, weight=10)
    ep2 = ServiceEndpoint(endpoint_id="ep-2", host="127.0.0.1", port=8081, weight=90)

    # Route 100 times to assert both targets are selected
    selected = set()
    for _ in range(100):
        target = router.route_request([ep1, ep2])
        selected.add(target.endpoint_id)

    assert "ep-1" in selected or "ep-2" in selected


def test_router_no_healthy_endpoints_raises() -> None:
    router = TrafficRouter()
    ep_unhealthy = ServiceEndpoint(endpoint_id="ep-1", host="127.0.0.1", port=8080, is_healthy=False)

    with pytest.raises(RoutingPolicyError):
        router.route_request([ep_unhealthy])
