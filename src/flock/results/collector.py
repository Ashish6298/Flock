"""Transport-independent result packet parser translating incoming envelopes into registry updates."""

import structlog
from typing import Dict, Any
from flock.types import NodeInfo
from flock.events.bus import EventBus
from flock.messaging.bus import MessageBus
from flock.messaging.models import MessageContext, MessageMetadata
from flock.messaging.handlers import MessageHandler
from flock.protocol.packet import MessageType
from flock.results.models import ExecutionResult, ResultMetadata, FailureResult
from flock.results.registry import ResultRegistry
from flock.results.serializer import ResultSerializer
from flock.results.exceptions import ChecksumMismatchError

logger = structlog.get_logger()

class ResultCollector:
    """Listens to message bus packets and registers results within catalog registry."""

    def __init__(
        self,
        node_id: str,
        message_bus: MessageBus,
        event_bus: EventBus,
        registry: ResultRegistry,
        serializer: ResultSerializer
    ) -> None:
        self.node_id = node_id
        self.bus = message_bus
        self.events = event_bus
        self.registry = registry
        self.serializer = serializer

        # Register message handlers in Router
        self.bus.router.register(MessageType.TASK_RESULT, _TaskResultHandler(self))
        self.bus.router.register(MessageType.TASK_RESULT_ACK, _TaskResultAckHandler())

    async def receive_result(self, result: ExecutionResult) -> None:
        """Register completed result value and dispatch alerts.

        Raises:
            ChecksumMismatchError: If hash verification fails.
        """
        # Validate checksum integrity
        expected_checksum = self.serializer.generate_checksum(result.serialized_value)
        if expected_checksum != result.checksum:
            raise ChecksumMismatchError(
                f"Result checksum validation failed for task {result.task_id}: "
                f"expected {expected_checksum}, got {result.checksum}"
            )

        self.registry.register_result(result)

        if result.success:
            await self.events.publish("task.completed", {"task_id": result.task_id})
            await self.events.publish("task.result.received", {"task_id": result.task_id})
        else:
            await self.events.publish("task.failed", {"task_id": result.task_id})


class _TaskResultHandler(MessageHandler):
    """Processes incoming completed task result packets."""

    def __init__(self, collector: ResultCollector) -> None:
        self.collector = collector

    async def handle(self, context: MessageContext) -> None:
        payload = context.payload
        task_id = payload["task_id"]
        raw_val = payload["serialized_value"]
        if isinstance(raw_val, str):
            # Resolve latin1 encoding representing raw byte parameters in JSON
            serialized_val = raw_val.encode("latin-1")
        else:
            serialized_val = bytes(raw_val)
        checksum = payload["checksum"]
        success = payload.get("success", True)
        
        duration = payload.get("duration_ms", 0.0)
        
        failure = None
        if not success and "failure" in payload:
            fail_data = payload["failure"]
            failure = FailureResult(
                exception_type=fail_data["exception_type"],
                exception_message=fail_data["exception_message"],
                traceback=fail_data.get("traceback", ""),
                retryable=fail_data.get("retryable", False),
                failure_stage=fail_data.get("failure_stage", "EXECUTION")
            )

        result = ExecutionResult(
            task_id=task_id,
            node_id=context.sender.node_id,
            completed_timestamp=payload.get("completed_timestamp", 0.0),
            duration_ms=duration,
            serialized_value=serialized_val,
            checksum=checksum,
            success=success,
            failure=failure
        )

        try:
            await self.collector.receive_result(result)
            
            # Send ACK reply
            reply_meta = MessageMetadata(correlation_id=context.metadata.request_id)
            reply_port = context.metadata.custom.get("reply_port", context.sender.port)
            reply_target = NodeInfo(node_id=context.sender.node_id, host=context.sender.host, port=reply_port)
            
            await self.collector.bus.send(
                reply_target,
                MessageType.TASK_RESULT_ACK,
                {"task_id": task_id, "status": "ACK"},
                reply_meta
            )
        except Exception as err:
            logger.error("Failed to collect task result packet", task_id=task_id, error=err)


class _TaskResultAckHandler(MessageHandler):
    """Placeholder handler for result acknowledgments."""

    async def handle(self, context: MessageContext) -> None:
        pass
