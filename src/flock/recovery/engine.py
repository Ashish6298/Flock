"""Core engine orchestrating failover task placements and messaging handshakes."""

import time
import asyncio
import structlog
from typing import Dict, Any, Optional
from flock.types import NodeInfo
from flock.events.bus import EventBus
from flock.messaging.bus import MessageBus
from flock.messaging.models import MessageContext, MessageMetadata
from flock.messaging.handlers import MessageHandler
from flock.protocol.packet import MessageType
from flock.cluster.service import ClusterMembershipService
from flock.cluster.models import ClusterMemberStatus
from flock.heartbeat.service import HeartbeatService
from flock.scheduler.service import TaskSchedulerService
from flock.scheduler.models import Task, TaskStatus
from flock.placement.engine import PlacementEngine
from flock.recovery.models import RetryPolicy, RetryContext, RecoveryPlan
from flock.recovery.registry import RecoveryRegistry
from flock.recovery.policy import RetryPolicyEngine
from flock.recovery.exceptions import UnrecoverableTaskError

logger = structlog.get_logger()

class RecoveryEngine:
    """Evaluates task completion failures and triggers failover reassignments."""

    def __init__(
        self,
        node_id: str,
        scheduler_service: TaskSchedulerService,
        placement_engine: PlacementEngine,
        membership_service: ClusterMembershipService,
        heartbeat_service: HeartbeatService,
        message_bus: MessageBus,
        event_bus: EventBus
    ) -> None:
        self.node_id = node_id
        self.scheduler = scheduler_service
        self.placement = placement_engine
        self.membership = membership_service
        self.heartbeat = heartbeat_service
        self.bus = message_bus
        self.events = event_bus

        self.registry = RecoveryRegistry()
        self.policy_engine = RetryPolicyEngine()

        # Register message handlers in Router
        self.bus.router.register(MessageType.TASK_RECOVERY_REQUEST, _TaskRecoveryRequestHandler(self))

    async def handle_execution_failure(self, task: Task, error_msg: str, exception_class: Optional[str] = None) -> None:
        """Process execution failure returns, check retry policies, and trigger re-route reassignments."""
        task_id = task.task_id
        ctx = self.registry.get_context(task_id)

        # Default policy: max attempts 3
        policy = RetryPolicy(max_attempts=3)
        decision = self.policy_engine.evaluate(policy, ctx, exception_class)

        if not decision.should_retry:
            logger.warn("Task retry parameters exhausted; marking dead letter", task_id=task_id, reason=decision.reason)
            self.scheduler.registry.update_status(task_id, TaskStatus.FAILED)
            await self.events.publish("task.deadletter.created", {"task_id": task_id})
            return

        # Prepare retry increment
        updated_ctx = RetryContext(
            task_id=task_id,
            attempt_count=ctx.attempt_count + 1,
            last_attempt_timestamp=time.time(),
            last_worker_id=task.creator_node_id,
            last_error_message=error_msg
        )
        self.registry.update_context(updated_ctx)

        # Trigger cooldown exclusions on failing worker node
        failing_node = task.creator_node_id
        self.registry.register_cooldown(failing_node, duration_sec=10.0)

        # Delay execution delay if configured
        if decision.delay_sec > 0.0:
            await self.events.publish("task.retry.scheduled", {"task_id": task_id, "delay": decision.delay_sec})
            await asyncio.sleep(decision.delay_sec)

        # Execute placement query
        await self.events.publish("task.retry.started", {"task_id": task_id})
        
        # Modify placement constraints temporarily if required, otherwise let placement engine run
        try:
            placement_decision = await self.placement.place_task(task, exclude_nodes=[failing_node])
            plan = RecoveryPlan(
                task_id=task_id,
                target_node_id=placement_decision.selected_node_id,
                exclude_workers=[failing_node]
            )
            self.registry.register_plan(plan)

            # Inform scheduler of completion recovery state updates
            await self.events.publish("task.recovery.completed", {"task_id": task_id})
        except Exception as err:
            logger.error("Failed to recover task placement assignment", task_id=task_id, error=err)
            await self.events.publish("task.retry.failed", {"task_id": task_id})


class _TaskRecoveryRequestHandler(MessageHandler):
    """Processes incoming task recovery queries."""

    def __init__(self, engine: RecoveryEngine) -> None:
        self.engine = engine

    async def handle(self, context: MessageContext) -> None:
        payload = context.payload
        task_id = payload["task_id"]
        
        # Publish event
        await self.engine.events.publish("task.recovery.started", {"task_id": task_id})

        # Send ACK reply
        reply_meta = MessageMetadata(correlation_id=context.metadata.request_id)
        reply_port = context.metadata.custom.get("reply_port", context.sender.port)
        reply_target = NodeInfo(node_id=context.sender.node_id, host=context.sender.host, port=reply_port)
        
        await self.engine.bus.send(
            reply_target,
            MessageType.TASK_RECOVERY_ACK,
            {"task_id": task_id, "status": "ACK"},
            reply_meta
        )
