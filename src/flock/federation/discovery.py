"""Cross-cluster discovery, capacity scanning, and advertisement management."""

from __future__ import annotations

import time
import threading
from typing import Dict, List, Optional
from flock.federation.exceptions import TopologyDiscoveryError
from flock.federation.models import ClusterAdvertisement


class FederationDiscoveryService:
    """Discovers geographical clusters and aggregates resource capability advertisements."""

    def __init__(self, local_cluster_id: str) -> None:
        self.local_cluster_id = local_cluster_id
        self._lock = threading.RLock()
        # cluster_id -> ClusterAdvertisement
        self._advertisements: Dict[str, ClusterAdvertisement] = {}

    def publish_advertisement(self, resource_summary: Dict[str, float]) -> ClusterAdvertisement:
        """Construct local advertisement for remote replication."""
        return ClusterAdvertisement(
            cluster_id=self.local_cluster_id,
            timestamp=time.time(),
            resource_summary=resource_summary,
        )

    def register_remote_advertisement(self, ad: ClusterAdvertisement) -> None:
        """Register a resource capability announcement received from a remote cluster."""
        with self._lock:
            self._advertisements[ad.cluster_id] = ad

    def get_advertisement(self, cluster_id: str) -> ClusterAdvertisement:
        """Get remote cluster's advertisement information."""
        with self._lock:
            if cluster_id not in self._advertisements:
                raise TopologyDiscoveryError(f"No advertisement found for cluster '{cluster_id}'.")
            return self._advertisements[cluster_id]

    def list_discovered_clusters(self) -> List[str]:
        """List all discovered federated cluster IDs."""
        with self._lock:
            return list(self._advertisements.keys())
