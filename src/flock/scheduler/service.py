"""Coordinator service implementing task submission, validation, queuing, and EventBus dispatches."""

import time
import uuid
import structlog
from typing import Dict, Any, List, Optional
from flock.types import NodeInfo
from flock.events.bus import EventBus
from flock.messaging.bus import MessageBus
from flock.messaging.models import MessageContext, MessageMetadata
from flock.messaging.handlers import MessageHandler
from flock.protocol.packet import MessageType
from flock.scheduler.models import Task, TaskMetadata, TaskStatus, SchedulingPolicy
from flock.scheduler.registry import TaskRegistry
from flock.scheduler.queue import SchedulingQueue
from flock.scheduler.exceptions import TaskValidationError

logger = structlog.get_logger()

class TaskSchedulerService:
    """Manages dynamic task submissions, validation constraints, and queuing lifecycles."""

    def __init__(
        self,
        node_id: str,
        message_bus: MessageBus,
        event_bus: EventBus,
        policy: SchedulingPolicy = SchedulingPolicy.FIFO,
        max_queue_size: int = 1000
    ) -> None:
        self.node_id = node_id
        self.bus = message_bus
        self.events = event_bus

        self.registry = TaskRegistry()
        self.queue = SchedulingQueue(policy=policy, max_size=max_queue_size)

        # Register message handlers in Router
        self.bus.router.register(MessageType.TASK_SUBMIT, _TaskSubmitHandler(self))
        self.bus.router.register(MessageType.TASK_ANNOUNCE, _TaskAnnounceHandler(self))

    async def submit_task(self, payload: Dict[str, Any], metadata: Optional[TaskMetadata] = None) -> Task:
        """Submit a task to the local scheduler queue.

        Raises:
            TaskValidationError: If validation checks fail.
        """
        task_id = str(uuid.uuid4())
        meta = metadata or TaskMetadata()
        
        # Validations
        if not payload:
            raise TaskValidationError("Task payload cannot be empty")
        if meta.execution_deadline and meta.execution_deadline < time.time():
            raise TaskValidationError("Task execution deadline cannot be in the past")

        task = Task(
            task_id=task_id,
            creator_node_id=self.node_id,
            payload=payload,
            metadata=meta,
            status=TaskStatus.VALIDATED,
            creation_timestamp=time.time()
        )

        self.registry.register(task)
        await self.events.publish("scheduler.task_created", {"task_id": task_id})

        # Transition to QUEUED
        self.registry.update_status(task_id, TaskStatus.QUEUED)
        # Fetch updated task object reflecting status changes
        updated_task = self.registry.get_task(task_id) or task
        self.queue.push(updated_task)
        await self.events.publish("scheduler.task_queued", {"task_id": task_id})

        return updated_task

    async def cancel_task(self, task_id: str) -> None:
        """Mark task as CANCELLED."""
        self.registry.update_status(task_id, TaskStatus.CANCELLED)
        await self.events.publish("scheduler.task_cancelled", {"task_id": task_id})


class _TaskSubmitHandler(MessageHandler):
    """Processes remote submissions and enqueues tasks."""

    def __init__(self, service: TaskSchedulerService) -> None:
        self.service = service

    async def handle(self, context: MessageContext) -> None:
        payload = context.payload
        task_payload = payload.get("payload", {})
        
        # Remote submit
        task = await self.service.submit_task(task_payload)
        
        reply_meta = MessageMetadata(correlation_id=context.metadata.request_id)
        reply_port = context.metadata.custom.get("reply_port", context.sender.port)
        reply_target = NodeInfo(node_id=context.sender.node_id, host=context.sender.host, port=reply_port)
        
        await self.service.bus.send(
            reply_target,
            MessageType.TASK_ANNOUNCE,
            {"task_id": task.task_id, "status": task.status.value},
            reply_meta
        )


class _TaskAnnounceHandler(MessageHandler):
    """Processes remote task updates."""

    def __init__(self, service: TaskSchedulerService) -> None:
        self.service = service

    async def handle(self, context: MessageContext) -> None:
        payload = context.payload
        task_id = payload["task_id"]
        status_val = payload["status"]
        
        # Sync local registry copy if exists
        existing = self.service.registry.get_task(task_id)
        if existing:
            self.service.registry.update_status(task_id, TaskStatus(status_val))
            await self.service.events.publish("scheduler.task_updated", {"task_id": task_id})
