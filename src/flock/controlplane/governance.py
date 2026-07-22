"""Governance policy evaluations and compliance checks reports."""

from __future__ import annotations

import threading
from typing import Dict, List, Optional
from flock.controlplane.exceptions import GovernancePolicyError
from flock.controlplane.models import GovernancePolicy


class GovernancePolicyManager:
    """Validates policy enforcement and evaluates rule criteria."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._policies: Dict[str, GovernancePolicy] = {}

    def register_policy(self, policy: GovernancePolicy) -> None:
        """Register a governance rule definition."""
        with self._lock:
            self._policies[policy.policy_id] = policy

    def get_policy(self, policy_id: str) -> Optional[GovernancePolicy]:
        """Get governance policy by ID."""
        with self._lock:
            return self._policies.get(policy_id)

    def evaluate_compliance(self, cluster_id: str, cluster_version: str) -> bool:
        """Evaluate if the cluster details satisfy registered governance policies (e.g. min version checks)."""
        with self._lock:
            for p in self._policies.values():
                if p.rule_name == "min_version_check":
                    min_version = p.parameters.get("min_version", "0.0.0")
                    # Simple comparison helper
                    if cluster_version < min_version:
                        if p.action_type == "enforce":
                            raise GovernancePolicyError(
                                f"Cluster '{cluster_id}' version '{cluster_version}' violates governance minimum version rule '{min_version}'."
                            )
                        return False
            return True

    def list_policies(self) -> List[GovernancePolicy]:
        """List registered governance policies."""
        with self._lock:
            return list(self._policies.values())
