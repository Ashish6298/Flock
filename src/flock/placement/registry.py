"""Authoritative container keeping latest placement decisions and mapping histories."""

import structlog
from typing import Dict, List, Optional
from flock.placement.models import AssignmentRecord, PlacementDecision
from flock.placement.exceptions import PlacementRegistryError

logger = structlog.get_logger()

class PlacementRegistry:
    """Asyncio-safe placement registry container tracking task-to-node assignments and acknowledgments."""

    def __init__(self) -> None:
        self._assignments: Dict[str, AssignmentRecord] = {}
        self._decisions: Dict[str, PlacementDecision] = {}

    def register_decision(self, decision: PlacementDecision) -> None:
        """Register task placement selection metrics."""
        self._decisions[decision.task_id] = decision
        logger.info("Registered placement decision", task_id=decision.task_id, target=decision.selected_node_id)

    def register_assignment(self, record: AssignmentRecord) -> None:
        """Register node task assignment."""
        self._assignments[record.task_id] = record
        logger.info("Registered task assignment record", task_id=record.task_id, node_id=record.node_id)

    def acknowledge_assignment(self, task_id: str) -> None:
        """Acknowledge task assignment.

        Raises:
            PlacementRegistryError: If task assignment record does not exist.
        """
        record = self._assignments.get(task_id)
        if not record:
            raise PlacementRegistryError(f"Task assignment record {task_id} not found")

        updated = AssignmentRecord(
            task_id=record.task_id,
            node_id=record.node_id,
            assigned_timestamp=record.assigned_timestamp,
            acknowledged=True,
            version=record.version + 1
        )
        self._assignments[task_id] = updated
        logger.info("Acknowledged task assignment", task_id=task_id, node_id=record.node_id)

    def get_assignment(self, task_id: str) -> Optional[AssignmentRecord]:
        """Look up active assignment parameters by task ID."""
        return self._assignments.get(task_id)

    def get_decision(self, task_id: str) -> Optional[PlacementDecision]:
        """Look up placement decision parameters by task ID."""
        return self._decisions.get(task_id)

    def list_assignments(self) -> List[AssignmentRecord]:
        """List active assignments."""
        return list(self._assignments.values())
