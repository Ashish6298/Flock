"""Fleet registry management and organization hierarchies."""

from __future__ import annotations

import threading
from typing import Dict, List, Optional
from flock.controlplane.exceptions import FleetRegistrationError
from flock.controlplane.models import FleetInfo


class FleetRegistry:
    """Manages creation, configuration, and enrollment of fleets under tenant organizations."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        # fleet_id -> FleetInfo
        self._fleets: Dict[str, FleetInfo] = {}

    def register_fleet(self, fleet: FleetInfo) -> None:
        """Register a new fleet definition."""
        with self._lock:
            if fleet.fleet_id in self._fleets:
                raise FleetRegistrationError(f"Fleet '{fleet.fleet_id}' is already registered.")
            self._fleets[fleet.fleet_id] = fleet

    def get_fleet(self, fleet_id: str) -> FleetInfo:
        """Get registered fleet metadata."""
        with self._lock:
            if fleet_id not in self._fleets:
                raise FleetRegistrationError(f"Fleet '{fleet_id}' not found.")
            return self._fleets[fleet_id]

    def list_fleets(self) -> List[FleetInfo]:
        """List all registered fleets."""
        with self._lock:
            return list(self._fleets.values())

    def unregister_fleet(self, fleet_id: str) -> None:
        """Remove a fleet from control plane registries."""
        with self._lock:
            if fleet_id not in self._fleets:
                raise FleetRegistrationError(f"Fleet '{fleet_id}' not found.")
            del self._fleets[fleet_id]
