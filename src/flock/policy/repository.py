"""Declarative policy document repository storage."""

from __future__ import annotations

import threading
from typing import Dict, List, Optional
from flock.policy.exceptions import PolicyError
from flock.policy.models import PolicyDefinition


class PolicyRepository:
    """Manages local policy storage, retrieval, and version definitions indexing."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        # policy_id -> PolicyDefinition
        self._policies: Dict[str, PolicyDefinition] = {}

    def store_policy(self, policy: PolicyDefinition) -> None:
        """Register a policy definition inside repository storage."""
        with self._lock:
            self._policies[policy.policy_id] = policy

    def get_policy(self, policy_id: str) -> PolicyDefinition:
        """Retrieve policy by identifier."""
        with self._lock:
            if policy_id not in self._policies:
                raise PolicyError(f"Policy '{policy_id}' not found in repository.")
            return self._policies[policy_id]

    def delete_policy(self, policy_id: str) -> None:
        """Delete policy by identifier."""
        with self._lock:
            if policy_id not in self._policies:
                raise PolicyError(f"Policy '{policy_id}' not found in repository.")
            del self._policies[policy_id]

    def list_policies(self) -> List[PolicyDefinition]:
        """List all active policies in the repository."""
        with self._lock:
            return list(self._policies.values())
