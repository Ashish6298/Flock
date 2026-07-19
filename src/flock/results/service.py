"""High-level result collection service orchestrating validators and wait routines."""

import time
import structlog
from typing import Dict, Any, Optional
from flock.types import NodeInfo
from flock.events.bus import EventBus
from flock.messaging.bus import MessageBus
from flock.messaging.models import MessageMetadata
from flock.results.models import ExecutionResult, ResultMetadata, FailureResult
from flock.results.registry import ResultRegistry
from flock.results.serializer import ResultSerializer
from flock.results.collector import ResultCollector
from flock.protocol.packet import MessageType

logger = structlog.get_logger()

class ResultService:
    """High-level API for submitting and asynchronously waiting for task results."""

    def __init__(
        self,
        node_id: str,
        message_bus: MessageBus,
        event_bus: EventBus,
        ttl_sec: float = 300.0
    ) -> None:
        self.node_id = node_id
        self.bus = message_bus
        self.events = event_bus

        self.registry = ResultRegistry(ttl_sec=ttl_sec)
        self.serializer = ResultSerializer()
        self.collector = ResultCollector(
            node_id=self.node_id,
            message_bus=self.bus,
            event_bus=self.events,
            registry=self.registry,
            serializer=self.serializer
        )

    async def submit_result(self, target: NodeInfo, task_id: str, value: Any) -> None:
        """Serialize result payload value and submit result to coordinator node."""
        serialized_val = self.serializer.serialize(value)
        # Convert raw bytes to latin-1 string to allow safe JSON serialization over network loopbacks
        payload_str = serialized_val.decode("latin-1")
        
        checksum = self.serializer.generate_checksum(serialized_val)

        payload = {
            "task_id": task_id,
            "success": True,
            "serialized_value": payload_str,
            "checksum": checksum,
            "completed_timestamp": time.time(),
            "duration_ms": 0.0
        }
        port_val = getattr(self.bus.transport, "port", 0)
        metadata = MessageMetadata(custom={"reply_port": port_val})
        await self.bus.send(target, MessageType.TASK_RESULT, payload, metadata)
        logger.info("Submitted task execution success result value", task_id=task_id, target=target.node_id)

    async def submit_failure(self, target: NodeInfo, task_id: str, error: Exception) -> None:
        """Submit task execution failure error detail to coordinator node."""
        payload = {
            "task_id": task_id,
            "success": False,
            "serialized_value": "",
            "checksum": self.serializer.generate_checksum(b""),
            "completed_timestamp": time.time(),
            "duration_ms": 0.0,
            "failure": {
                "exception_type": type(error).__name__,
                "exception_message": str(error),
                "traceback": "",
                "retryable": False,
                "failure_stage": "EXECUTION"
            }
        }
        port_val = getattr(self.bus.transport, "port", 0)
        metadata = MessageMetadata(custom={"reply_port": port_val})
        await self.bus.send(target, MessageType.TASK_RESULT, payload, metadata)
        logger.info("Submitted task execution failure result value", task_id=task_id, target=target.node_id)

    async def wait_for_result(self, task_id: str, timeout_sec: float = 10.0) -> Any:
        """Asynchronously block until result completes and deserialize return value."""
        result = await self.registry.wait_for_result(task_id, timeout_sec)
        if not result.success:
            raise RuntimeError(
                f"Task {task_id} execution failed: "
                f"{result.failure.exception_type if result.failure else 'Unknown'}: "
                f"{result.failure.exception_message if result.failure else ''}"
            )
        return self.serializer.deserialize(result.serialized_value)

    def get_result(self, task_id: str) -> Optional[Any]:
        """Look up completed result; returns None if not registered or failed."""
        record = self.registry.get_result(task_id)
        if record and record.success:
            return self.serializer.deserialize(record.serialized_value)
        return None

    def cleanup(self) -> None:
        """Trigger registry cleanup routines."""
        self.registry.cleanup_expired_entries()

    def shutdown(self) -> None:
        """Shutdown service metrics and registries."""
        self.registry.clear()
