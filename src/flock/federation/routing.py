"""Global Routing Engine selecting appropriate target clusters."""

from __future__ import annotations

import uuid
from typing import List, Optional

from flock.federation.exceptions import FederationRoutingError
from flock.federation.models import FederationCluster, RoutingDecision


class GlobalRoutingEngine:
    """Evaluates cluster metrics to select destination clusters for global tasks."""

    def __init__(self) -> None:
        pass

    def route_task(self, task_id: str, source_cluster: str, candidates: List[FederationCluster]) -> RoutingDecision:
        """Route task to candidate cluster with highest capacity score.

        Raises:
            FederationRoutingError: If no candidate clusters are registered.
        """
        healthy_candidates = [c for c in candidates if c.is_healthy]
        if not healthy_candidates:
            raise FederationRoutingError("No healthy target clusters available to route global task.")

        # Sort by capacity_score descending
        sorted_clusters = sorted(healthy_candidates, key=lambda c: c.capacity_score, reverse=True)
        best_dest = sorted_clusters[0]

        return RoutingDecision(
            decision_id=str(uuid.uuid4()),
            task_id=task_id,
            source_cluster=source_cluster,
            destination_cluster=best_dest.cluster_id,
        )
