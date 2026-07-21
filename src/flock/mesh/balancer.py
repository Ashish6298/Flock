"""Load Balancer Engine selecting targets."""

from __future__ import annotations

import threading
from typing import Dict, List

from flock.mesh.exceptions import RoutingPolicyError
from flock.mesh.models import ServiceEndpoint


class LoadBalancingEngine:
    """Provides Round Robin and Least Connections selection strategies."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        
        # service_id -> index offset
        self._offsets: Dict[str, int] = {}
        # endpoint_id -> active connection count
        self._active_connections: Dict[str, int] = {}

    def select_round_robin(self, service_id: str, endpoints: List[ServiceEndpoint]) -> ServiceEndpoint:
        """Select endpoint sequentially.

        Raises:
            RoutingPolicyError: If endpoints list is empty.
        """
        healthy = [ep for ep in endpoints if ep.is_healthy]
        if not healthy:
            raise RoutingPolicyError("No healthy endpoints available.")

        with self._lock:
            idx = self._offsets.get(service_id, 0)
            target = healthy[idx % len(healthy)]
            self._offsets[service_id] = (idx + 1) % len(healthy)
            return target

    def select_least_connections(self, endpoints: List[ServiceEndpoint]) -> ServiceEndpoint:
        """Select endpoint with lowest active connection count.

        Raises:
            RoutingPolicyError: If endpoints list is empty.
        """
        healthy = [ep for ep in endpoints if ep.is_healthy]
        if not healthy:
            raise RoutingPolicyError("No healthy endpoints available.")

        with self._lock:
            # Sort by connection count
            sorted_eps = sorted(
                healthy,
                key=lambda ep: self._active_connections.get(ep.endpoint_id, 0),
            )
            return sorted_eps[0]

    def increment_connections(self, endpoint_id: str) -> None:
        """Increment connections count."""
        with self._lock:
            count = self._active_connections.get(endpoint_id, 0)
            self._active_connections[endpoint_id] = count + 1

    def decrement_connections(self, endpoint_id: str) -> None:
        """Decrement connections count."""
        with self._lock:
            count = self._active_connections.get(endpoint_id, 0)
            if count > 0:
                self._active_connections[endpoint_id] = count - 1
