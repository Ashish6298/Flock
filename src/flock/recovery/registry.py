"""Authoritative catalog keeping retry histories and active recovery plans."""

import time
import structlog
from typing import Dict, Optional, List
from flock.recovery.models import RetryContext, RecoveryPlan
from flock.recovery.exceptions import DuplicateRecoveryError

logger = structlog.get_logger()

class RecoveryRegistry:
    """Asyncio-safe registry tracking active task recovery plans and history contexts."""

    def __init__(self) -> None:
        self._contexts: Dict[str, RetryContext] = {}
        self._plans: Dict[str, RecoveryPlan] = {}
        self._cooldowns: Dict[str, float] = {}

    def get_context(self, task_id: str) -> RetryContext:
        """Lookup retry context; returns fresh record if not present."""
        return self._contexts.get(task_id, RetryContext(task_id=task_id))

    def update_context(self, context: RetryContext) -> None:
        """Save updated retry context coordinates."""
        self._contexts[context.task_id] = context
        logger.info("Updated retry context details", task_id=context.task_id, attempt=context.attempt_count)

    def register_plan(self, plan: RecoveryPlan) -> None:
        """Register failover recovery execution plan.

        Raises:
            DuplicateRecoveryError: If recovery is already active for task.
        """
        if plan.task_id in self._plans:
            raise DuplicateRecoveryError(f"Recovery plan for task {plan.task_id} is already active")
        self._plans[plan.task_id] = plan
        logger.info("Registered task recovery plan", task_id=plan.task_id, target=plan.target_node_id)

    def get_plan(self, task_id: str) -> Optional[RecoveryPlan]:
        """Lookup active recovery plan."""
        return self._plans.get(task_id)

    def remove_plan(self, task_id: str) -> None:
        """Remove plan from inventory once complete."""
        self._plans.pop(task_id, None)

    def register_cooldown(self, node_id: str, duration_sec: float) -> None:
        """Exclude node from failover targets temporarily."""
        self._cooldowns[node_id] = time.time() + duration_sec
        logger.info("Registered node failover cooldown exclusion", node_id=node_id, duration=duration_sec)

    def is_cooling_down(self, node_id: str) -> bool:
        """Verify if node exclusion has expired."""
        expiry = self._cooldowns.get(node_id, 0.0)
        return time.time() < expiry

    def clear(self) -> None:
        """Clear all active plans and registry logs."""
        self._contexts.clear()
        self._plans.clear()
        self._cooldowns.clear()
