"""Authoritative container keeping latest task metadata details."""

import structlog
from typing import Dict, List, Optional
from flock.scheduler.models import Task, TaskStatus
from flock.scheduler.exceptions import InvalidTaskStateTransitionError

logger = structlog.get_logger()

class TaskRegistry:
    """Asyncio-safe task registry container tracking tasks and scheduling transitions."""

    def __init__(self) -> None:
        self._tasks: Dict[str, Task] = {}

    def register(self, task: Task) -> None:
        """Register task details."""
        self._tasks[task.task_id] = task
        logger.info("Registered task", task_id=task.task_id, status=task.status)

    def update_status(self, task_id: str, new_status: TaskStatus) -> None:
        """Deterministic state transition checks.

        Raises:
            InvalidTaskStateTransitionError: If requesting an illegal transition.
        """
        task = self._tasks.get(task_id)
        if not task:
            raise InvalidTaskStateTransitionError(f"Task {task_id} not registered")

        current = task.status
        # Transition check rules
        if current in (TaskStatus.CANCELLED, TaskStatus.EXPIRED):
            raise InvalidTaskStateTransitionError(f"Cannot transition task {task_id} from terminal state {current}")

        updated = Task(
            task_id=task.task_id,
            creator_node_id=task.creator_node_id,
            payload=task.payload,
            metadata=task.metadata,
            status=new_status,
            creation_timestamp=task.creation_timestamp
        )
        self._tasks[task_id] = updated
        logger.info("Updated task status", task_id=task_id, from_status=current, to_status=new_status)

    def get_task(self, task_id: str) -> Optional[Task]:
        """Retrieve task details by ID."""
        return self._tasks.get(task_id)

    def list_tasks(self, status: Optional[TaskStatus] = None) -> List[Task]:
        """List tasks matching filter criteria."""
        if status:
            return [t for t in self._tasks.values() if t.status == status]
        return list(self._tasks.values())
