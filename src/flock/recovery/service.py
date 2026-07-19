"""High-level orchestration service exposing failover and recovery controls."""

import structlog
from typing import Dict, Any, Optional
from flock.types import NodeInfo
from flock.events.bus import EventBus
from flock.messaging.bus import MessageBus
from flock.messaging.models import MessageMetadata
from flock.protocol.packet import MessageType
from flock.scheduler.models import Task
from flock.recovery.engine import RecoveryEngine
from flock.recovery.models import RecoveryPlan

logger = structlog.get_logger()

class RecoveryService:
    """High-level API for triggering task failovers and recovery queries."""

    def __init__(self, engine: RecoveryEngine) -> None:
        self.engine = engine

    async def schedule_retry(self, task: Task, error_msg: str) -> None:
        """Evaluate and launch retry pipeline."""
        await self.engine.handle_execution_failure(task, error_msg)

    async def recover_task(self, target: NodeInfo, task_id: str) -> None:
        """Submit recovery request query to coordinator node."""
        payload = {"task_id": task_id}
        port_val = getattr(self.engine.bus.transport, "port", 0)
        metadata = MessageMetadata(custom={"reply_port": port_val})
        await self.engine.bus.send(target, MessageType.TASK_RECOVERY_REQUEST, payload, metadata)
        logger.info("Submitted task recovery request packet", task_id=task_id, target=target.node_id)

    def get_recovery_plan(self, task_id: str) -> Optional[RecoveryPlan]:
        """Lookup active recovery plan details."""
        return self.engine.registry.get_plan(task_id)

    def cleanup(self) -> None:
        """Evict catalog entries."""
        self.engine.registry.clear()

    def shutdown(self) -> None:
        """Shutdown registry."""
        self.engine.registry.clear()
