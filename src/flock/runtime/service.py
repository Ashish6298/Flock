"""Coordinator service managing local task execution, states, and event notifications."""

import asyncio
import time
import structlog
from typing import Dict, Any, List, Optional, Callable
from flock.events.bus import EventBus
from flock.messaging.bus import MessageBus
from flock.messaging.models import MessageContext
from flock.messaging.handlers import MessageHandler
from flock.protocol.packet import MessageType
from flock.scheduler.models import Task, TaskStatus
from flock.runtime.models import WorkerInfo, ExecutionState
from flock.runtime.context import ExecutionContext
from flock.runtime.executor import Executor, ThreadPoolExecutorBackend
from flock.runtime.exceptions import ExecutionStateError

logger = structlog.get_logger()

class WorkerRuntimeService:
    """Manages worker registries, execution contexts, and local queue dispatches."""

    def __init__(
        self,
        node_id: str,
        message_bus: MessageBus,
        event_bus: EventBus,
        executor: Optional[Executor] = None
    ) -> None:
        self.node_id = node_id
        self.bus = message_bus
        self.events = event_bus
        self.executor = executor or ThreadPoolExecutorBackend(max_workers=4)

        self._workers: Dict[str, WorkerInfo] = {}
        self._contexts: Dict[str, ExecutionContext] = {}
        self._states: Dict[str, ExecutionState] = {}
        self._running = False

    async def start(self) -> None:
        """Start local runtime worker service."""
        self._running = True
        logger.info("WorkerRuntimeService started", node_id=self.node_id)

    async def stop(self) -> None:
        """Cancel active executions and shutdown local pools."""
        self._running = False
        # Cancel all active contexts
        for ctx in list(self._contexts.values()):
            ctx.request_cancel()
        
        # Shutdown pool if thread pool backend
        if isinstance(self.executor, ThreadPoolExecutorBackend):
            self.executor.shutdown()
        logger.info("WorkerRuntimeService stopped", node_id=self.node_id)

    def register_worker(self, worker: WorkerInfo) -> None:
        """Register local worker details."""
        self._workers[worker.worker_id] = worker
        logger.info("Registered local runtime worker", worker_id=worker.worker_id)

    def get_execution_state(self, task_id: str) -> Optional[ExecutionState]:
        """Lookup active task execution state."""
        return self._states.get(task_id)

    def update_execution_state(self, task_id: str, state: ExecutionState) -> None:
        """Advance local task execution state."""
        self._states[task_id] = state
        logger.info("Updated execution state", task_id=task_id, state=state)

    async def execute_task(self, task: Task, func: Callable[..., Any], *args: Any) -> Any:
        """Execute task locally using registered backend pool.

        Raises:
            ExecutionStateError: If task execution fails.
        """
        task_id = task.task_id
        self.update_execution_state(task_id, ExecutionState.ACCEPTED)
        await self.events.publish("runtime.task_accepted", {"task_id": task_id})

        ctx = ExecutionContext(
            task_id=task_id,
            execution_deadline=task.metadata.execution_deadline
        )
        self._contexts[task_id] = ctx
        
        self.update_execution_state(task_id, ExecutionState.RUNNING)
        await self.events.publish("runtime.task_running", {"task_id": task_id})

        try:
            res = await self.executor.submit(func, *args, context=ctx)
            self.update_execution_state(task_id, ExecutionState.COMPLETED)
            await self.events.publish("runtime.task_completed", {"task_id": task_id})
            return res
        except asyncio.CancelledError:
            self.update_execution_state(task_id, ExecutionState.CANCELLED)
            await self.events.publish("runtime.task_cancelled", {"task_id": task_id})
            raise
        except Exception as err:
            self.update_execution_state(task_id, ExecutionState.FAILED)
            await self.events.publish("runtime.task_failed", {"task_id": task_id, "error": str(err)})
            raise ExecutionStateError(f"Task execution failed: {err}") from err
        finally:
            self._contexts.pop(task_id, None)

    async def request_cancellation(self, task_id: str) -> None:
        """Request cancel on context token."""
        ctx = self._contexts.get(task_id)
        if ctx:
            self.update_execution_state(task_id, ExecutionState.CANCELLING)
            ctx.request_cancel()
            logger.info("Requested task cancellation", task_id=task_id)
