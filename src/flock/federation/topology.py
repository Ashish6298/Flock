"""Hybrid mesh geographical and network cluster layout manager."""

from __future__ import annotations

import time
import threading
from typing import Dict, List, Optional
from flock.federation.exceptions import TopologyDiscoveryError
from flock.federation.models import FederationCluster, FederationTopology


class FederationTopologyManager:
    """Maintains geographically aware network latency matrix configurations."""

    def __init__(self, local_cluster_id: str) -> None:
        self.local_cluster_id = local_cluster_id
        self._lock = threading.RLock()
        self._clusters: Dict[str, FederationCluster] = {}
        self._latency_matrix: Dict[str, Dict[str, float]] = {}  # source -> target -> ms
        self._seq = 0

    def register_cluster(self, cluster: FederationCluster) -> None:
        """Register cluster metadata inside topology maps."""
        with self._lock:
            self._clusters[cluster.cluster_id] = cluster

    def update_link_latency(self, source_id: str, target_id: str, latency_ms: float) -> None:
        """Update network latency between geographically remote clusters."""
        with self._lock:
            sources = self._latency_matrix.setdefault(source_id, {})
            sources[target_id] = latency_ms

    def get_link_latency(self, source_id: str, target_id: str) -> float:
        """Get ping latency in milliseconds, defaulting to 10.0 ms if unconfigured."""
        with self._lock:
            return self._latency_matrix.get(source_id, {}).get(target_id, 10.0)

    def get_topology(self) -> FederationTopology:
        """Generate a strongly typed FederationTopology snapshot."""
        with self._lock:
            self._seq += 1
            return FederationTopology(
                topology_id=f"top-{self._seq}",
                timestamp=time.time(),
                clusters=list(self._clusters.values()),
                latency_matrix={k: dict(v) for k, v in self._latency_matrix.items()},
            )
