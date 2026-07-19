"""Placement pipeline engine orchestrating node evaluations and handshakes."""

import time
import structlog
from typing import Dict, Any, List, Optional
from flock.types import NodeInfo
from flock.events.bus import EventBus
from flock.messaging.bus import MessageBus
from flock.messaging.models import MessageContext, MessageMetadata
from flock.messaging.handlers import MessageHandler
from flock.protocol.packet import MessageType
from flock.cluster.service import ClusterMembershipService
from flock.cluster.models import ClusterMemberStatus
from flock.heartbeat.service import HeartbeatService
from flock.heartbeat.models import HealthState
from flock.scheduler.service import TaskSchedulerService
from flock.scheduler.models import Task, TaskStatus
from flock.placement.models import (
    PlacementDecision,
    AssignmentRecord,
    PlacementPolicy,
    NodeCapability
)
from flock.placement.registry import PlacementRegistry
from flock.placement.exceptions import NoEligibleNodesError, AssignmentRejectedError

logger = structlog.get_logger()

class PlacementEngine:
    """Evaluates cluster topologies and handles dynamic assignments."""

    def __init__(
        self,
        node_id: str,
        membership_service: ClusterMembershipService,
        heartbeat_service: HeartbeatService,
        scheduler_service: TaskSchedulerService,
        message_bus: MessageBus,
        event_bus: EventBus
    ) -> None:
        self.node_id = node_id
        self.membership = membership_service
        self.heartbeat = heartbeat_service
        self.scheduler = scheduler_service
        self.bus = message_bus
        self.events = event_bus

        self.registry = PlacementRegistry()
        self._capabilities: Dict[str, NodeCapability] = {}

        # Register message handlers in Router
        self.bus.router.register(MessageType.TASK_ASSIGN, _TaskAssignHandler(self))
        self.bus.router.register(MessageType.TASK_ASSIGN_ACK, _TaskAssignAckHandler(self))

    def register_node_capability(self, capability: NodeCapability) -> None:
        """Register custom capabilities metadata parameters for a cluster node."""
        self._capabilities[capability.node_id] = capability

    def get_node_capability(self, node_id: str) -> NodeCapability:
        """Lookup node capabilities; returns default fallback if not registered."""
        return self._capabilities.get(node_id, NodeCapability(node_id=node_id))

    async def place_task(self, task: Task, exclude_nodes: Optional[List[str]] = None) -> PlacementDecision:
        """Evaluate task placement and broadcast assignment over messaging pipeline.

        Raises:
            NoEligibleNodesError: If no healthy node satisfies constraints.
        """
        logger.info("Starting task placement pipeline", task_id=task.task_id)
        await self.events.publish("placement.started", {"task_id": task.task_id})

        # Stage 1: Get healthy nodes
        active_members = self.membership.registry.list_members(ClusterMemberStatus.ACTIVE)
        candidates = []

        excludes = exclude_nodes or []
        for member in active_members:
            if member.node_id in excludes:
                continue
            # Check reachability in heartbeat registry
            health = self.heartbeat.registry.get_record(member.node_id)
            if member.node_id == self.node_id or (health and health.state == HealthState.HEALTHY):
                candidates.append(member.node_id)

        if not candidates:
            raise NoEligibleNodesError(f"No healthy eligible nodes available for task {task.task_id}")

        # Stage 2: Filter by constraints (e.g. required operating system tags)
        required_tags = task.metadata.constraints.required_capabilities
        eligible = []

        for cid in candidates:
            cap = self.get_node_capability(cid)
            # Match capability tags
            match = True
            for tag in required_tags:
                if tag not in cap.supported_tags:
                    match = False
                    break
            if match:
                eligible.append(cid)

        if not eligible:
            raise NoEligibleNodesError(f"No nodes satisfy task constraints for task {task.task_id}")

        # Stage 3: Apply selection policy
        selected_node = eligible[0]  # First Healthy Node baseline policy

        decision = PlacementDecision(
            task_id=task.task_id,
            selected_node_id=selected_node,
            policy_used=PlacementPolicy.FIRST_HEALTHY,
            timestamp=time.time()
        )
        self.registry.register_decision(decision)

        # Stage 4: Register assignment
        record = AssignmentRecord(
            task_id=task.task_id,
            node_id=selected_node,
            assigned_timestamp=time.time()
        )
        self.registry.register_assignment(record)

        # Transition task state to ASSIGNED
        self.scheduler.registry.update_status(task.task_id, TaskStatus.ASSIGNED)

        # Stage 5: Dispatch assign message if remote worker
        if selected_node != self.node_id:
            member_info = self.membership.registry.get_member(selected_node)
            if member_info:
                target = NodeInfo(
                    node_id=selected_node,
                    host=member_info.description.host,
                    port=member_info.description.port
                )
                payload = {"task_id": task.task_id, "creator_node_id": task.creator_node_id}
                metadata = MessageMetadata(custom={"reply_port": self.membership.desc.port})
                await self.bus.send(target, MessageType.TASK_ASSIGN, payload, metadata)

        await self.events.publish("placement.assigned", {"task_id": task.task_id, "node_id": selected_node})
        return decision


class _TaskAssignHandler(MessageHandler):
    """Processes incoming assignment payloads and returns acknowledgments."""

    def __init__(self, engine: PlacementEngine) -> None:
        self.engine = engine

    async def handle(self, context: MessageContext) -> None:
        payload = context.payload
        task_id = payload["task_id"]
        
        # Build local assignment record representation on worker side
        record = AssignmentRecord(
            task_id=task_id,
            node_id=self.engine.node_id,
            assigned_timestamp=time.time(),
            acknowledged=True
        )
        self.engine.registry.register_assignment(record)

        # Publish EventBus details
        await self.engine.events.publish("placement.assign_received", {"task_id": task_id})

        # Send ACK back
        reply_meta = MessageMetadata(correlation_id=context.metadata.request_id)
        reply_port = context.metadata.custom.get("reply_port", context.sender.port)
        reply_target = NodeInfo(node_id=context.sender.node_id, host=context.sender.host, port=reply_port)
        
        await self.engine.bus.send(
            reply_target,
            MessageType.TASK_ASSIGN_ACK,
            {"task_id": task_id, "status": "ACK"},
            reply_meta
        )


class _TaskAssignAckHandler(MessageHandler):
    """Processes incoming task assignment acknowledgments."""

    def __init__(self, engine: PlacementEngine) -> None:
        self.engine = engine

    async def handle(self, context: MessageContext) -> None:
        payload = context.payload
        task_id = payload["task_id"]
        
        self.engine.registry.acknowledge_assignment(task_id)
        await self.engine.events.publish("placement.assign_acknowledged", {"task_id": task_id})
