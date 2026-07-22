"""Authorization Engine extending RBAC/ABAC models and evaluating policies dynamically."""

from __future__ import annotations

import re
import threading
from typing import Dict, Set, List, Any, Optional
from flock.security.exceptions import AuthorizationError
from flock.security.models import AccessDecision, SecurityPolicy


class AuthorizationEngine:
    """Enforces fine-grained Zero-Trust Role-Based and Attribute-Based Access Control policies."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        # role -> Set of permissions
        self._roles: Dict[str, Set[str]] = {
            "coordinator": {"tasks.create", "tasks.cancel", "cluster.read", "metrics.read", "secrets.read", "quarantine.manage"},
            "worker": {"tasks.execute", "metrics.write", "secrets.read"},
            "observer": {"cluster.read", "metrics.read"},
        }
        # node_id -> assigned role
        self._assignments: Dict[str, str] = {}
        # Dynamic policies list
        self._policies: List[SecurityPolicy] = []

    def assign_role(self, subject_id: str, role: str) -> None:
        """Assign an RBAC role to a subject identifier (node or service account)."""
        with self._lock:
            if role not in self._roles:
                raise AuthorizationError(f"Role '{role}' is not registered in authorization engine.")
            self._assignments[subject_id] = role

    def add_policy(self, policy: SecurityPolicy) -> None:
        """Add a dynamic security policy (RBAC or ABAC)."""
        with self._lock:
            self._policies.append(policy)

    def remove_policy(self, policy_id: str) -> None:
        """Remove a dynamic policy by ID."""
        with self._lock:
            self._policies = [p for p in self._policies if p.policy_id != policy_id]

    def authorize(
        self,
        subject_id: str,
        required_permission: str,
        attributes: Optional[Dict[str, Any]] = None,
    ) -> AccessDecision:
        """Evaluate access decision based on RBAC and dynamic policy engines.
        
        Args:
            subject_id: The identity requesting access.
            required_permission: The permission string (e.g. tasks.create).
            attributes: Subject/Resource/Environment attributes for ABAC rules.
        """
        with self._lock:
            # 1. Evaluate Dynamic Policies first (both Allow/Deny and ABAC rules)
            # Deny policies always win (Zero-Trust principle)
            attrs = attributes or {}
            
            deny_decision = self._evaluate_dynamic_policies(subject_id, required_permission, attrs, effect="deny")
            if deny_decision:
                return deny_decision

            allow_decision = self._evaluate_dynamic_policies(subject_id, required_permission, attrs, effect="allow")
            if allow_decision:
                return allow_decision

            # 2. Fall back to standard static RBAC
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

    def _evaluate_dynamic_policies(
        self,
        subject_id: str,
        permission: str,
        attributes: Dict[str, Any],
        effect: str,
    ) -> Optional[AccessDecision]:
        """Search policies matching subject/action and check attributes constraints."""
        for p in self._policies:
            if p.effect.lower() != effect.lower():
                continue

            # Check action pattern (permission match)
            action_match = False
            for act_pattern in p.actions:
                if act_pattern == "*" or act_pattern == permission:
                    action_match = True
                    break
                # Simple wildcard matching
                regex = "^" + re.escape(act_pattern).replace(r"\*", ".*") + "$"
                if re.match(regex, permission):
                    action_match = True
                    break

            if not action_match:
                continue

            # Check subject pattern match
            subject_match = False
            for sub_pattern in p.subjects:
                if sub_pattern == "*" or sub_pattern == subject_id:
                    subject_match = True
                    break
                regex = "^" + re.escape(sub_pattern).replace(r"\*", ".*") + "$"
                if re.match(regex, subject_id):
                    subject_match = True
                    break

            if not subject_match:
                continue

            # Check dynamic attributes conditions (ABAC matching)
            condition_passed = True
            for attr_key, expected_val in p.conditions.items():
                actual_val = attributes.get(attr_key)
                # Sub-matching constraints
                if actual_val != expected_val:
                    condition_passed = False
                    break

            if condition_passed:
                allowed_state = (effect.lower() == "allow")
                return AccessDecision(
                    allowed=allowed_state,
                    reason=f"Matched policy '{p.policy_id}' with effect '{p.effect}' for '{permission}'.",
                    required_permission=permission,
                )

        return None
