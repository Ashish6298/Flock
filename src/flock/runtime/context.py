"""Context models wrapping environment settings, deadlines, and cancellation tokens."""

import asyncio
from typing import Dict, Any, Optional

class ExecutionContext:
    """Contains environmental variables, deadlines, and cancellation tokens for task containment."""

    def __init__(
        self,
        task_id: str,
        execution_deadline: Optional[float] = None,
        env_vars: Optional[Dict[str, Any]] = None
    ) -> None:
        self.task_id = task_id
        self.execution_deadline = execution_deadline
        self.env_vars = env_vars or {}
        
        # Asyncio cancel event mapping
        self._cancel_event = asyncio.Event()

    def request_cancel(self) -> None:
        """Trigger cancellation event signal."""
        self._cancel_event.set()

    def is_cancelled(self) -> bool:
        """Check if cancel signal has been requested."""
        return self._cancel_event.is_set()

    def check_cancellation(self) -> None:
        """Helper to raise cancelled error immediately if flagged."""
        if self.is_cancelled():
            raise asyncio.CancelledError(f"Task execution context {self.task_id} cancellation requested")
