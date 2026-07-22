"""Policy bundles aggregation manager."""

from __future__ import annotations

import threading
from typing import Dict, List, Optional
from flock.policy.models import PolicyDefinition


class PolicyBundleManager:
    """Manages publishing and grouping related policy documents into deployment bundles."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        # bundle_id -> list of policy definitions
        self._bundles: Dict[str, List[PolicyDefinition]] = {}

    def publish_bundle(self, bundle_id: str, policies: List[PolicyDefinition]) -> None:
        """Publish a group of policies as a bundle."""
        with self._lock:
            self._bundles[bundle_id] = list(policies)

    def get_bundle(self, bundle_id: str) -> List[PolicyDefinition]:
        """Retrieve a policy bundle by ID."""
        with self._lock:
            return list(self._bundles.get(bundle_id, []))
