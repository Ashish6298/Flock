"""Unit tests for LoadBalancingEngine."""

import pytest
from flock.mesh.balancer import LoadBalancingEngine
from flock.mesh.models import ServiceEndpoint


def test_round_robin_selection() -> None:
    balancer = LoadBalancingEngine()
    ep1 = ServiceEndpoint(endpoint_id="ep-1", host="127.0.0.1", port=8080)
    ep2 = ServiceEndpoint(endpoint_id="ep-2", host="127.0.0.1", port=8081)

    # 1st selection
    selected_1 = balancer.select_round_robin("service-1", [ep1, ep2])
    assert selected_1 == ep1

    # 2nd selection -> alternates
    selected_2 = balancer.select_round_robin("service-1", [ep1, ep2])
    assert selected_2 == ep2


def test_least_connections_selection() -> None:
    balancer = LoadBalancingEngine()
    ep1 = ServiceEndpoint(endpoint_id="ep-1", host="127.0.0.1", port=8080)
    ep2 = ServiceEndpoint(endpoint_id="ep-2", host="127.0.0.1", port=8081)

    balancer.increment_connections("ep-1")
    balancer.increment_connections("ep-1")

    # ep-2 has 0 connections, so it must be selected
    target = balancer.select_least_connections([ep1, ep2])
    assert target == ep2
