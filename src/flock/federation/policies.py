"""Cross-cluster security and workload routing policy enforcement rules."""

from __future__ import annotations

import threading
from typing import Dict, List, Optional
from flock.federation.exceptions import FederationPolicyViolationError
from flock.federation.models import FederationPolicy


class FederationPolicyManager:
    """Stores and evaluates global federation boundary policies."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._policies: Dict[str, FederationPolicy] = {}

    def register_policy(self, policy: FederationPolicy) -> None:
        """Register a cross-cluster boundary constraint policy."""
        with self._lock:
            self._policies[policy.policy_id] = policy

    def get_policy(self, policy_id: str) -> Optional[FederationPolicy]:
        with self._lock:
            return self._policies.get(policy_id)

    def validate_routing_policy(
        self,
        action: str,
        source_cluster: str,
        destination_cluster: str,
        latency_ms: float,
    ) -> bool:
        """Ensure task placement decisions do not violate security or latency policies.
        
        Raises:
            FederationPolicyViolationError: If constraint checks are violated.
        """
        with self._lock:
            for p in self._policies.values():
                # Check target cluster matches destination
                cluster_match = False
                for tc in p.target_clusters:
                    if tc == "*" or tc == destination_cluster:
                        cluster_match = True
                        break
                if not cluster_match:
                    continue
                    
                # Check action restrictions
                action_allowed = False
                for act in p.allowed_actions:
                    if act == "*" or act == action:
                        action_allowed = True
                        break
                if not action_allowed:
                    raise FederationPolicyViolationError(
                        f"Action '{action}' is blocked by policy '{p.policy_id}' for destination cluster '{destination_cluster}'."
                    )
                    
                # Check latency policy boundaries
                if latency_ms > p.max_cross_region_latency_ms:
                    raise FederationPolicyViolationError(
                        f"Latency boundary violated: {latency_ms}ms exceeds maximum limits of {p.max_cross_region_latency_ms}ms defined by policy '{p.policy_id}'."
                    )
            return True
