"""Coordinator service executing periodic ping transmissions and evaluating responses."""

import asyncio
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
from flock.heartbeat.models import HealthRecord, HealthState
from flock.heartbeat.registry import HealthRegistry
from flock.heartbeat.failure_detector import FailureDetector

logger = structlog.get_logger()

class HeartbeatService:
    """Manages active ping intervals and coordinates reachability checks."""

    def __init__(
        self,
        node_id: str,
        membership_service: ClusterMembershipService,
        message_bus: MessageBus,
        event_bus: EventBus,
        ping_interval_sec: float = 1.0,
        ping_timeout_sec: float = 0.5,
        max_missed_count: int = 3
    ) -> None:
        self.node_id = node_id
        self.membership = membership_service
        self.bus = message_bus
        self.events = event_bus
        self.ping_interval = ping_interval_sec
        self.ping_timeout = ping_timeout_sec

        self.registry = HealthRegistry()
        self.detector = FailureDetector(
            registry=self.registry,
            event_bus=self.events,
            ping_timeout_sec=ping_timeout_sec,
            max_missed_count=max_missed_count
        )

        self._task: Optional[asyncio.Task[None]] = None
        self._running = False

        # Register message handlers in Router
        self.bus.router.register(MessageType.HEARTBEAT_PING, _PingRequestHandler(self))
        self.bus.router.register(MessageType.HEARTBEAT_PONG, _PongResponseHandler(self))

    async def start(self) -> None:
        """Start scheduler transmitting ping heartbeats to active members."""
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._broadcast_loop())
        logger.info("HeartbeatService scheduler started", node_id=self.node_id)

    async def stop(self) -> None:
        """Cancel heartbeat transmission scheduler cleanly."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("HeartbeatService scheduler stopped", node_id=self.node_id)

    async def _broadcast_loop(self) -> None:
        """Periodic background evaluation loop."""
        while self._running:
            try:
                # Retrieve active members from membership
                active_members = self.membership.registry.list_members(ClusterMemberStatus.ACTIVE)
                
                for member in active_members:
                    if member.node_id == self.node_id:
                        continue
                    
                    # Ensure node exists in health registry
                    record = self.registry.get_record(member.node_id)
                    if not record:
                        self.registry.set_record(
                            HealthRecord(
                                node_id=member.node_id,
                                state=HealthState.HEALTHY,
                                last_heartbeat_timestamp=time.time()
                            )
                        )

                    # Send Ping Message
                    target = NodeInfo(
                        node_id=member.node_id,
                        host=member.description.host,
                        port=member.description.port
                    )
                    
                    payload = {"node_id": self.node_id, "timestamp": time.time()}
                    metadata = MessageMetadata(custom={"reply_port": self.membership.desc.port})
                    
                    # Fire evaluation first to check timeouts
                    await self.detector.evaluate_node(member.node_id)
                    
                    try:
                        await self.bus.send(target, MessageType.HEARTBEAT_PING, payload, metadata)
                    except Exception as err:
                        logger.debug("Failed outbound heartbeat ping", target=member.node_id, error=err)

            except Exception as err:
                logger.error("Error in heartbeat loop execution", error=err)

            await asyncio.sleep(self.ping_interval)


class _PingRequestHandler(MessageHandler):
    """Replies directly to inbound pings with pongs."""

    def __init__(self, service: HeartbeatService) -> None:
        self.service = service

    async def handle(self, context: MessageContext) -> None:
        payload = context.payload
        reply_meta = MessageMetadata(correlation_id=context.metadata.request_id)
        reply_port = context.metadata.custom.get("reply_port", context.sender.port)
        reply_target = NodeInfo(node_id=context.sender.node_id, host=context.sender.host, port=reply_port)
        
        pong_payload = {
            "node_id": self.service.node_id,
            "timestamp": payload.get("timestamp", time.time())
        }
        await self.service.bus.send(reply_target, MessageType.HEARTBEAT_PONG, pong_payload, reply_meta)


class _PongResponseHandler(MessageHandler):
    """Processes incoming responses, calculating round-trip-time and resetting failure counters."""

    def __init__(self, service: HeartbeatService) -> None:
        self.service = service

    async def handle(self, context: MessageContext) -> None:
        payload = context.payload
        node_id = payload["node_id"]
        sent_ts = payload.get("timestamp", 0.0)
        
        rtt = 0.0
        if sent_ts > 0:
            rtt = (time.time() - sent_ts) * 1000.0

        await self.service.detector.record_heartbeat_success(node_id, rtt)
