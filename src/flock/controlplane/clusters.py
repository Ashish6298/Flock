"""Fleet cluster enrollments, updates tracking, and labels queries."""

from __future__ import annotations

import threading
from typing import Dict, List, Optional
from flock.controlplane.exceptions import ClusterEnrollmentError
from flock.controlplane.models import EnrolledCluster


class ClusterEnrollmentManager:
    """Manages active clusters enrolled inside the fleet catalog."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        # cluster_id -> EnrolledCluster
        self._clusters: Dict[str, EnrolledCluster] = {}

    def enroll_cluster(self, cluster: EnrolledCluster) -> None:
        """Enroll a cluster into the fleet registry."""
        with self._lock:
            self._clusters[cluster.cluster_id] = cluster

    def update_cluster_heartbeat(self, cluster_id: str, last_seen: float) -> None:
        """Update last seen heartbeat timestamp for an enrolled cluster."""
        with self._lock:
            cluster = self._clusters.get(cluster_id)
            if not cluster:
                raise ClusterEnrollmentError(f"Cluster '{cluster_id}' is not enrolled.")
            
            # Construct a new immutable instance to reflect update
            self._clusters[cluster_id] = EnrolledCluster(
                cluster_id=cluster.cluster_id,
                fleet_id=cluster.fleet_id,
                name=cluster.name,
                version=cluster.version,
                labels=cluster.labels,
                features_active=cluster.features_active,
                last_seen=last_seen,
            )

    def get_cluster(self, cluster_id: str) -> EnrolledCluster:
        """Get enrolled cluster metadata details."""
        with self._lock:
            if cluster_id not in self._clusters:
                raise ClusterEnrollmentError(f"Cluster '{cluster_id}' is not enrolled.")
            return self._clusters[cluster_id]

    def list_enrolled_clusters(self) -> List[EnrolledCluster]:
        """List all active enrolled clusters."""
        with self._lock:
            return list(self._clusters.values())

    def remove_cluster(self, cluster_id: str) -> None:
        """Disenroll a cluster from fleet registration."""
        with self._lock:
            if cluster_id not in self._clusters:
                raise ClusterEnrollmentError(f"Cluster '{cluster_id}' is not enrolled.")
            del self._clusters[cluster_id]
