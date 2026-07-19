"""Authoritative container keeping latest reachability health metrics."""

import structlog
from typing import Dict, List, Optional
from flock.heartbeat.models import HealthRecord, HealthState
from flock.heartbeat.exceptions import HealthStateTransitionError

logger = structlog.get_logger()

class HealthRegistry:
    """Asyncio-safe registry tracking immutable health records and validated state transitions."""

    def __init__(self) -> None:
        self._records: Dict[str, HealthRecord] = {}

    def set_record(self, record: HealthRecord) -> None:
        """Upsert health record details.

        Raises:
            HealthStateTransitionError: If requesting an illegal transition.
        """
        node_id = record.node_id
        existing = self._records.get(node_id)
        if existing:
            # Validate state transitions
            if existing.state == HealthState.UNREACHABLE and record.state == HealthState.HEALTHY:
                # Must transition through RECOVERING first
                raise HealthStateTransitionError(
                    f"Illegal transition for {node_id} directly from UNREACHABLE to HEALTHY"
                )
            
        self._records[node_id] = record

    def get_record(self, node_id: str) -> Optional[HealthRecord]:
        """Retrieve health status records."""
        return self._records.get(node_id)

    def list_records(self, state: Optional[HealthState] = None) -> List[HealthRecord]:
        """List health record details matching criteria filters."""
        if state:
            return [r for r in self._records.values() if r.state == state]
        return list(self._records.values())

    def clear(self) -> None:
        """Clear all metrics."""
        self._records.clear()
