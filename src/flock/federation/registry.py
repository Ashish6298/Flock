"""Federation Registry for tracking active clusters."""

from __future__ import annotations

import threading
from typing import Dict, List, Optional

from flock.federation.exceptions import ClusterUnavailableError
from flock.federation.models import FederationCluster


class FederationRegistry:
    """Thread-safe registration directory keeping list of member clusters."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        
        # cluster_id -> FederationCluster
        self._clusters: Dict[str, FederationCluster] = {}

    def register_cluster(self, cluster: FederationCluster) -> None:
        """Register or update a member cluster profile."""
        with self._lock:
            self._clusters[cluster.cluster_id] = cluster

    def unregister_cluster(self, cluster_id: str) -> None:
        """Remove a cluster from the federation."""
        with self._lock:
            self._clusters.pop(cluster_id, None)

    def get_cluster(self, cluster_id: str) -> Optional[FederationCluster]:
        """Fetch registered cluster parameters."""
        with self._lock:
            return self._clusters.get(cluster_id)

    def list_clusters(self) -> List[FederationCluster]:
        """List all registered clusters."""
        with self._lock:
            return list(self._clusters.values())
