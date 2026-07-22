"""Disaster recovery planning and backup retention policy configurations."""

from __future__ import annotations

import threading
from typing import Dict, List, Optional
from flock.recovery.models import RetentionPolicy


class RecoveryPolicyManager:
    """Manages disaster recovery and data retention policies."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._policies: Dict[str, RetentionPolicy] = {}

    def register_policy(self, policy: RetentionPolicy) -> None:
        """Register a retention policy configuration."""
        with self._lock:
            self._policies[policy.policy_id] = policy

    def get_policy(self, policy_id: str) -> Optional[RetentionPolicy]:
        """Retrieve a registered policy by ID."""
        with self._lock:
            return self._policies.get(policy_id)

    def list_policies(self) -> List[RetentionPolicy]:
        """List all active retention policies."""
        with self._lock:
            return list(self._policies.values())
