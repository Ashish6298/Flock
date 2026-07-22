"""Dynamic feature flags management, activation rules, and parameters."""

from __future__ import annotations

import threading
from typing import Dict, List, Set, Optional


class FeatureFlagManager:
    """Manages global feature toggles and dynamic rollout rules across clusters."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        # flag_name -> enabled status (bool)
        self._flags: Dict[str, bool] = {}
        # flag_name -> set of cluster_ids targeted
        self._flag_targets: Dict[str, Set[str]] = {}

    def define_flag(self, name: str, default_enabled: bool = False) -> None:
        """Create a new feature flag definition."""
        with self._lock:
            if name not in self._flags:
                self._flags[name] = default_enabled
                self._flag_targets[name] = set()

    def enable_flag(self, name: str) -> None:
        """Enable a feature flag globally."""
        with self._lock:
            self.define_flag(name)
            self._flags[name] = True

    def disable_flag(self, name: str) -> None:
        """Disable a feature flag globally."""
        with self._lock:
            self.define_flag(name)
            self._flags[name] = False

    def target_flag_to_cluster(self, name: str, cluster_id: str) -> None:
        """Explicitly target flag activation to a specific cluster ID."""
        with self._lock:
            self.define_flag(name)
            self._flag_targets[name].add(cluster_id)

    def is_feature_enabled(self, name: str, cluster_id: Optional[str] = None) -> bool:
        """Evaluate if the feature flag is currently active (globally or for the cluster)."""
        with self._lock:
            if name not in self._flags:
                return False
            # Check global flag status
            if self._flags[name]:
                return True
            # Check explicit cluster targeting status
            if cluster_id and cluster_id in self._flag_targets.get(name, set()):
                return True
            return False
