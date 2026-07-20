"""Resource Registry maintaining live capacities for CPU, memory, and GPUs."""

from __future__ import annotations

import threading
from typing import Dict, List, Optional

from flock.resources.models import NodeResourceProfile


class ResourceRegistry:
    """Thread-safe catalog tracking live resource profiles of active cluster members."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        
        # node_id -> NodeResourceProfile
        self._profiles: Dict[str, NodeResourceProfile] = {}

    def register_node(self, profile: NodeResourceProfile) -> None:
        """Register or update a node's resource utilization profile."""
        with self._lock:
            self._profiles[profile.node_id] = profile

    def unregister_node(self, node_id: str) -> None:
        """Remove a node's metrics profile from the inventory."""
        with self._lock:
            self._profiles.pop(node_id, None)

    def get_profile(self, node_id: str) -> Optional[NodeResourceProfile]:
        """Fetch node resource profile by node identifier."""
        with self._lock:
            return self._profiles.get(node_id)

    def list_profiles(self) -> List[NodeResourceProfile]:
        """List all active node resource profiles."""
        with self._lock:
            return list(self._profiles.values())
