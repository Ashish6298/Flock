"""AutoScaler triggering cluster size changes."""

from __future__ import annotations

import time
import uuid
from typing import Optional

from flock.orchestrator.exceptions import ScalingPolicyViolationError
from flock.orchestrator.models import ClusterSnapshot, ScalingDecision


class AutoScaler:
    """Monitors queue sizes and load trends to trigger node scale recommendations."""

    def __init__(self, min_nodes: int = 1, max_nodes: int = 10) -> None:
        self.min_nodes = min_nodes
        self.max_nodes = max_nodes

    def evaluate_scale(self, snapshot: ClusterSnapshot) -> Optional[ScalingDecision]:
        """Compute autoscaling decision updates.

        Raises:
            ScalingPolicyViolationError: If scale decision violates min/max bounds.
        """
        current_size = len(snapshot.active_nodes)
        
        # Scale out on high utilization
        if snapshot.avg_utilization > 80.0:
            if current_size >= self.max_nodes:
                raise ScalingPolicyViolationError("Scale-out limit reached, cannot allocate nodes.")
            
            return ScalingDecision(
                decision_id=str(uuid.uuid4()),
                node_id="autoscaled-node-out",
                scale_type="SCALE_OUT",
                size_change=1,
                timestamp=time.time(),
            )

        # Scale in on extremely low utilization
        if snapshot.avg_utilization < 20.0 and current_size > self.min_nodes:
            return ScalingDecision(
                decision_id=str(uuid.uuid4()),
                node_id=snapshot.active_nodes[-1],
                scale_type="SCALE_IN",
                size_change=-1,
                timestamp=time.time(),
            )

        return None
