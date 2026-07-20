"""Authorization Engine implementing Role-Based Access Control (RBAC)."""

from __future__ import annotations

from typing import Dict, Set

from flock.security.exceptions import AuthorizationError
from flock.security.models import AccessDecision


class AuthorizationEngine:
    """Evaluates RBAC queries based on defined role-to-permission mappings."""

    def __init__(self) -> None:
        # role -> Set of permissions
        self._roles: Dict[str, Set[str]] = {
            "coordinator": {"tasks.create", "tasks.cancel", "cluster.read", "metrics.read"},
            "worker": {"tasks.execute", "metrics.write"},
            "observer": {"cluster.read", "metrics.read"},
        }
        # node_id -> assigned role
        self._assignments: Dict[str, str] = {}

    def assign_role(self, subject_id: str, role: str) -> None:
        """Assign an RBAC role to a subject identifier (node or service account)."""
        if role not in self._roles:
            raise AuthorizationError(f"Role '{role}' is not registered in authorization engine.")
        self._assignments[subject_id] = role

    def authorize(self, subject_id: str, required_permission: str) -> AccessDecision:
        """Evaluate if the subject possesses the required permission.

        Returns:
            AccessDecision detailing allowed status and reason.
        """
        role = self._assignments.get(subject_id, "observer")
        permissions = self._roles.get(role, set())

        if required_permission in permissions:
            return AccessDecision(
                allowed=True,
                reason=f"Subject '{subject_id}' has role '{role}' possessing permission '{required_permission}'.",
                required_permission=required_permission,
            )
        
        return AccessDecision(
            allowed=False,
            reason=f"Subject '{subject_id}' role '{role}' does not possess required permission '{required_permission}'.",
            required_permission=required_permission,
        )
