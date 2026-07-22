"""Remediation planner and approval workflow exceptions manager."""

from __future__ import annotations

import threading
from typing import Dict, List, Set, Any, Optional


class RemediationPlanner:
    """Aggregates policy violation remediations and coordinates execution commands."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._plans: Dict[str, str] = {}  # resource_id -> plan description

    def register_remediation(self, resource_id: str, plan_text: str) -> None:
        with self._lock:
            self._plans[resource_id] = plan_text

    def get_remediation_plan(self, resource_id: str) -> Optional[str]:
        with self._lock:
            return self._plans.get(resource_id)
class PolicyApprovalWorkflow:
    """Manages policy exception approval overrides states."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        # policy_id -> set of approved exception cluster IDs
        self._exceptions: Dict[str, Set[str]] = {}

    def approve_exception(self, policy_id: str, cluster_id: str) -> None:
        """Approve a policy violation override exception for a target cluster."""
        with self._lock:
            exceptions = self._exceptions.setdefault(policy_id, set())
            exceptions.add(cluster_id)

    def has_exception(self, policy_id: str, cluster_id: str) -> bool:
        """Return True if the cluster has a registered policy bypass exception."""
        with self._lock:
            return cluster_id in self._exceptions.get(policy_id, set())
