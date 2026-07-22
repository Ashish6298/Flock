"""Business continuity planning, failover coordination, and node recoveries orchestration."""

from __future__ import annotations

import time
import threading
from typing import Any, Dict, List, Optional
from flock.recovery.exceptions import ContinuityError


class BusinessContinuityPlanner:
    """Manages active disaster plan configurations, failover coordination, and recovery steps."""

    def __init__(self, node_id: str) -> None:
        self.node_id = node_id
        self._lock = threading.RLock()
        self._active_plan: Optional[str] = None
        self._failover_in_progress = False
        self._failover_history: List[Dict[str, Any]] = []

    def initiate_failover(self, target_leader_node: str, reason: str) -> None:
        """Trigger cluster failover routing and activate continuity plan."""
        with self._lock:
            if self._failover_in_progress:
                raise ContinuityError("Failover operation is already in progress.")
            self._failover_in_progress = True
            self._active_plan = f"failover-to-{target_leader_node}"
            
            self._failover_history.append({
                "plan_id": self._active_plan,
                "timestamp": time.time(),
                "initiated_by": self.node_id,
                "target_node": target_leader_node,
                "reason": reason,
                "status": "started",
            })

    def complete_failover(self) -> None:
        """Mark the active failover procedure as completed."""
        with self._lock:
            if not self._failover_in_progress:
                raise ContinuityError("No active failover operation in progress to complete.")
            self._failover_in_progress = False
            
            # Update last history log
            if self._failover_history:
                self._failover_history[-1]["status"] = "completed"
                self._failover_history[-1]["completed_at"] = time.time()

    def get_failover_status(self) -> Dict[str, Any]:
        """Return the current cluster continuity failover parameters."""
        with self._lock:
            return {
                "failover_in_progress": self._failover_in_progress,
                "active_plan": self._active_plan,
                "history": list(self._failover_history),
            }
