"""Policy Engine mapping cluster constraints to policies."""

from __future__ import annotations

from typing import Dict

from flock.orchestrator.models import ClusterPolicy


class PolicyEngine:
    """Stores and evaluates global placement configurations."""

    def __init__(self, default_policy: ClusterPolicy) -> None:
        self._policy = default_policy

    def update_policy(self, policy: ClusterPolicy) -> None:
        """Update active policy rules."""
        self._policy = policy

    def get_policy(self) -> ClusterPolicy:
        """Fetch current policy details."""
        return self._policy

    def evaluate_violation(self, current_utilization: float) -> bool:
        """Assert if metric properties exceed policy threshold parameters."""
        return current_utilization > self._policy.target_utilization
