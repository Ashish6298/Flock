"""ResourceBalancer periodically evaluating cluster utilization skew."""

from __future__ import annotations

import uuid
from typing import List, Optional

from flock.resources.models import BalancingDecision, NodeResourceProfile


class ResourceBalancer:
    """Detects overloaded and underutilized nodes, planning migrations."""

    def __init__(self, imbalance_threshold: float = 30.0) -> None:
        self.imbalance_threshold = imbalance_threshold

    def evaluate_skew(self, nodes: List[NodeResourceProfile]) -> Optional[BalancingDecision]:
        """Detect utilization variance skew to emit migration decisions.

        Returns:
            Optional BalancingDecision if skew threshold is crossed.
        """
        if len(nodes) < 2:
            return None

        # Find min and max CPU loaded nodes
        sorted_nodes = sorted(nodes, key=lambda n: n.cpu_util)
        min_node = sorted_nodes[0]
        max_node = sorted_nodes[-1]

        # Calculate load variance skew
        skew = max_node.cpu_util - min_node.cpu_util

        if skew >= self.imbalance_threshold:
            # Emit migration decision recommendation
            return BalancingDecision(
                recommendation_id=str(uuid.uuid4()),
                source_node=max_node.node_id,
                target_node=min_node.node_id,
                # Place task migration placeholder
                task_id="auto-migrated-task-0",
            )

        return None
