"""Traffic Router handling weighted canary deployments."""

from __future__ import annotations

import random
from typing import List

from flock.mesh.exceptions import RoutingPolicyError
from flock.mesh.models import ServiceEndpoint


class TrafficRouter:
    """Selects route paths matching percentage weights."""

    def __init__(self) -> None:
        pass

    def route_request(self, endpoints: List[ServiceEndpoint]) -> ServiceEndpoint:
        """Select endpoint using weighted random choice logic.

        Raises:
            RoutingPolicyError: If endpoints list is empty.
        """
        healthy_endpoints = [ep for ep in endpoints if ep.is_healthy]
        if not healthy_endpoints:
            raise RoutingPolicyError("No healthy endpoints available to route request.")

        total_weight = sum(ep.weight for ep in healthy_endpoints)
        if total_weight <= 0:
            raise RoutingPolicyError("Cumulative route weights must be greater than zero.")

        val = random.randint(1, total_weight)
        current = 0
        for ep in healthy_endpoints:
            current += ep.weight
            if val <= current:
                return ep

        return healthy_endpoints[0]
