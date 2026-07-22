"""Zero-Trust Security policy management and evaluation engine."""

from __future__ import annotations

import threading
from typing import Dict, List
from flock.security.exceptions import PolicyEvaluationError
from flock.security.models import SecurityPolicy
from flock.security.authorization import AuthorizationEngine


class PolicyManager:
    """Manages system-wide Zero-Trust authorization policies."""

    def __init__(self, auth_engine: AuthorizationEngine) -> None:
        self._auth_engine = auth_engine
        self._lock = threading.RLock()
        self._policies: Dict[str, SecurityPolicy] = {}

    def add_policy(self, policy: SecurityPolicy) -> None:
        """Register a new policy and wire it to the authorization engine."""
        with self._lock:
            self._policies[policy.policy_id] = policy
            self._auth_engine.add_policy(policy)

    def remove_policy(self, policy_id: str) -> None:
        """Remove a security policy by ID."""
        with self._lock:
            if policy_id not in self._policies:
                raise PolicyEvaluationError(f"Policy '{policy_id}' not found.")
            del self._policies[policy_id]
            self._auth_engine.remove_policy(policy_id)

    def list_policies(self) -> List[SecurityPolicy]:
        """List all active security policies."""
        with self._lock:
            return list(self._policies.values())

    def get_policy(self, policy_id: str) -> SecurityPolicy:
        """Get security policy by ID."""
        with self._lock:
            if policy_id not in self._policies:
                raise PolicyEvaluationError(f"Policy '{policy_id}' not found.")
            return self._policies[policy_id]
