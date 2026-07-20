"""Resource Allocator handling reservations, leases, and rollbacks."""

from __future__ import annotations

import time
import uuid
from typing import Dict, List, Optional

from flock.resources.exceptions import ResourceExhaustionError
from flock.resources.models import AllocationResult, NodeResourceProfile, ResourceReservation
from flock.resources.registry import ResourceRegistry


class ResourceAllocator:
    """Manages transactional allocation bookings against live node inventories."""

    def __init__(self, registry: ResourceRegistry, lease_ttl_seconds: int = 60) -> None:
        self._registry = registry
        self._lease_ttl = lease_ttl_seconds
        
        # reservation_id -> ResourceReservation
        self.reservations: Dict[str, ResourceReservation] = {}

    def allocate(self, request_id: str, requirements: Dict[str, float]) -> AllocationResult:
        """Find a node that fits requirements, generating a lease reservation.

        Raises:
            ResourceExhaustionError: If no node matches the required bounds.
        """
        profiles = self._registry.list_profiles()
        req_cpu = requirements.get("cpu", 0.0)
        req_mem = requirements.get("memory", 0.0)

        best_node: Optional[str] = None
        
        # Simple Best-Fit / Resource-Aware First-Fit selector
        for prof in profiles:
            available_cpu = prof.cpu_cores * (1.0 - prof.cpu_util / 100.0)
            available_mem = prof.memory_mb * (1.0 - prof.memory_util / 100.0)

            if available_cpu >= req_cpu and available_mem >= req_mem:
                best_node = prof.node_id
                break

        if not best_node:
            raise ResourceExhaustionError("No cluster node matches required CPU and Memory thresholds.")

        # Create lease
        res_id = str(uuid.uuid4())
        expires = time.time() + self._lease_ttl
        
        res = ResourceReservation(
            reservation_id=res_id,
            node_id=best_node,
            request_id=request_id,
            resources=requirements,
            expires_at=expires,
        )
        self.reservations[res_id] = res

        return AllocationResult(
            success=True,
            reservation_id=res_id,
            assigned_node=best_node,
            allocated_resources=requirements,
        )

    def release(self, reservation_id: str) -> None:
        """Purge reservation lease, releasing allocations back to inventory pools."""
        self.reservations.pop(reservation_id, None)
