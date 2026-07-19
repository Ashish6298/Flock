"""Coordinating Cluster Membership Service pipeline rules."""

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
from flock.discovery.service import DiscoveryService
from flock.discovery.models import NodeDescription
from flock.cluster.models import ClusterMember, ClusterMemberStatus
from flock.cluster.registry import MembershipRegistry
from flock.cluster.exceptions import SnapshotValidationError

logger = structlog.get_logger()

class ClusterMembershipService:
    """Orchestrates join procedures, processes departures, and synchronizes membership states."""

    def __init__(
        self,
        node_id: str,
        discovery_service: DiscoveryService,
        message_bus: MessageBus,
        event_bus: EventBus
    ) -> None:
        self.node_id = node_id
        self.discovery = discovery_service
        self.bus = message_bus
        self.events = event_bus
        self.registry = MembershipRegistry()
        
        # Self Node description reference
        self.desc = self.discovery.get_self_description()
        
        # Add self to local registry as ACTIVE
        self.registry.add_member(
            ClusterMember(
                node_id=self.node_id,
                description=self.desc,
                status=ClusterMemberStatus.ACTIVE,
                join_timestamp=time.time(),
                role="worker"
            )
        )

        # Wire discovery events notifications
        self.discovery.register_discovered_callback(self._on_peer_discovered)
        self.discovery.register_expired_callback(self._on_peer_expired)

        # Registry handler mapping entries in Router
        self.bus.router.register(MessageType.MEMBER_JOIN_REQ, _JoinRequestHandler(self))
        self.bus.router.register(MessageType.MEMBER_JOIN_ACK, _JoinAckHandler(self))
        self.bus.router.register(MessageType.MEMBER_SNAPSHOT_REQ, _SnapshotRequestHandler(self))
        self.bus.router.register(MessageType.MEMBER_SNAPSHOT_RESP, _SnapshotResponseHandler(self))

    async def join_cluster(self, target: NodeInfo) -> None:
        """Asynchronously send membership join request."""
        logger.info("Initiating join procedure to cluster target", target=target.node_id)
        
        payload = {
            "node_id": self.node_id,
            "host": self.desc.host,
            "port": self.desc.port,
            "protocol_version": self.desc.protocol_version,
            "framework_version": self.desc.framework_version,
            "startup_timestamp": self.desc.startup_timestamp
        }
        
        # Set reply port metadata so loopbacks find client correctly
        metadata = MessageMetadata(custom={"reply_port": self.desc.port})
        await self.bus.send(target, MessageType.MEMBER_JOIN_REQ, payload, metadata)

    async def broadcast_leave(self) -> None:
        """Inform active cluster members of graceful departure."""
        payload = {"node_id": self.node_id}
        
        for member in self.registry.list_members(ClusterMemberStatus.ACTIVE):
            if member.node_id == self.node_id:
                continue
            try:
                target = NodeInfo(node_id=member.node_id, host=member.description.host, port=member.description.port)
                await self.bus.send(target, MessageType.MEMBER_LEAVE_NOTIFY, payload)
            except Exception as err:
                logger.debug("Failed exit notification dispatch", peer=member.node_id, error=err)

    def get_snapshot(self) -> List[Dict[str, Any]]:
        """Serialize current cluster membership catalog snapshot list."""
        snapshot = []
        for m in self.registry.list_members():
            snapshot.append({
                "node_id": m.node_id,
                "status": m.status.value,
                "join_timestamp": m.join_timestamp,
                "membership_version": m.membership_version,
                "role": m.role,
                "description": {
                    "node_id": m.description.node_id,
                    "host": m.description.host,
                    "port": m.description.port,
                    "protocol_version": m.description.protocol_version,
                    "framework_version": m.description.framework_version
                }
            })
        return snapshot

    async def sync_snapshot(self, snapshot: List[Dict[str, Any]]) -> None:
        """Synchronize snapshot into registry."""
        for entry in snapshot:
            try:
                node_id = entry["node_id"]
                if node_id == self.node_id:
                    continue
                
                desc_data = entry["description"]
                desc = NodeDescription(
                    node_id=desc_data["node_id"],
                    host=desc_data["host"],
                    port=desc_data["port"],
                    protocol_version=desc_data.get("protocol_version", 1),
                    framework_version=desc_data.get("framework_version", "0.1.0")
                )
                
                existing = self.registry.get_member(node_id)
                if not existing:
                    new_member = ClusterMember(
                        node_id=node_id,
                        description=desc,
                        status=ClusterMemberStatus(entry["status"]),
                        join_timestamp=entry["join_timestamp"],
                        membership_version=entry.get("membership_version", 1),
                        role=entry.get("role", "worker")
                    )
                    self.registry.add_member(new_member)
                    # Notify EventBus locally
                    await self.events.publish("cluster.member_added", {"node_id": node_id})
                else:
                    # Version check comparison
                    incoming_ver = entry.get("membership_version", 1)
                    if incoming_ver > existing.membership_version:
                        self.registry.update_status(node_id, ClusterMemberStatus(entry["status"]))
                        await self.events.publish("cluster.member_updated", {"node_id": node_id})
            except Exception as err:
                raise SnapshotValidationError(f"Invalid membership entry parsing snapshot: {err}") from err

    async def _on_peer_discovered(self, desc: NodeDescription) -> None:
        """Discovery notification callback - Auto trigger join flow if not registered."""
        existing = self.registry.get_member(desc.node_id)
        if not existing:
            target = NodeInfo(node_id=desc.node_id, host=desc.host, port=desc.port)
            await self.join_cluster(target)

    async def _on_peer_expired(self, node_id: str) -> None:
        """Discovery cleanup expiration notification callback."""
        existing = self.registry.get_member(node_id)
        if existing and existing.status == ClusterMemberStatus.ACTIVE:
            self.registry.remove_member(node_id)
            await self.events.publish("cluster.member_removed", {"node_id": node_id})


class _JoinRequestHandler(MessageHandler):
    """Answers incoming join queries and responses with acknowledgements."""

    def __init__(self, service: ClusterMembershipService) -> None:
        self.service = service

    async def handle(self, context: MessageContext) -> None:
        payload = context.payload
        node_id = payload["node_id"]
        
        desc = NodeDescription(
            node_id=node_id,
            host=payload["host"],
            port=payload["port"],
            protocol_version=payload.get("protocol_version", 1),
            framework_version=payload.get("framework_version", "0.1.0"),
            startup_timestamp=payload.get("startup_timestamp", 0.0)
        )
        
        # Add to local catalog registry
        existing = self.service.registry.get_member(node_id)
        if not existing:
            member = ClusterMember(
                node_id=node_id,
                description=desc,
                status=ClusterMemberStatus.ACTIVE,
                join_timestamp=time.time(),
                role="worker"
            )
            self.service.registry.add_member(member)
        else:
            self.service.registry.update_status(node_id, ClusterMemberStatus.ACTIVE)

        # Notify EventBus locally
        await self.service.events.publish("cluster.member_joined", {"node_id": node_id})

        # Send join acknowledgement back
        ack_payload = {
            "node_id": self.service.node_id,
            "snapshot": self.service.get_snapshot()
        }
        
        reply_meta = MessageMetadata(
            correlation_id=context.metadata.request_id,
            custom={"reply_port": self.service.desc.port}
        )
        reply_port = context.metadata.custom.get("reply_port", context.sender.port)
        reply_target = NodeInfo(node_id=context.sender.node_id, host=context.sender.host, port=reply_port)
        await self.service.bus.send(reply_target, MessageType.MEMBER_JOIN_ACK, ack_payload, reply_meta)


class _JoinAckHandler(MessageHandler):
    """Processes incoming join acknowledgements and merges cluster snapshots."""

    def __init__(self, service: ClusterMembershipService) -> None:
        self.service = service

    async def handle(self, context: MessageContext) -> None:
        payload = context.payload
        node_id = payload["node_id"]
        
        # Register sender as active member
        desc = self.service.discovery.registry.get_peer(node_id)
        if not desc:
            # Reconstruct from snapshot details if available
            snapshot = payload.get("snapshot", [])
            sender_entry = next((item for item in snapshot if item["node_id"] == node_id), None)
            if sender_entry:
                desc_data = sender_entry["description"]
                desc = NodeDescription(
                    node_id=desc_data["node_id"],
                    host=desc_data["host"],
                    port=desc_data["port"],
                    protocol_version=desc_data.get("protocol_version", 1),
                    framework_version=desc_data.get("framework_version", "0.1.0")
                )
            else:
                # Use custom metadata reply port if available to map port config correctly
                reply_port = context.metadata.custom.get("reply_port", context.sender.port)
                desc = NodeDescription(node_id=node_id, host=context.sender.host, port=reply_port)
        
        existing = self.service.registry.get_member(node_id)
        if not existing:
            member = ClusterMember(
                node_id=node_id,
                description=desc,
                status=ClusterMemberStatus.ACTIVE,
                join_timestamp=time.time()
            )
            self.service.registry.add_member(member)
        else:
            self.service.registry.update_status(node_id, ClusterMemberStatus.ACTIVE)
        
        await self.service.events.publish("cluster.member_joined", {"node_id": node_id})
        
        # Merge remote cluster snapshot
        snapshot = payload.get("snapshot", [])
        await self.service.sync_snapshot(snapshot)


class _SnapshotRequestHandler(MessageHandler):
    """Returns local cluster snapshot."""

    def __init__(self, service: ClusterMembershipService) -> None:
        self.service = service

    async def handle(self, context: MessageContext) -> None:
        reply_meta = MessageMetadata(correlation_id=context.metadata.request_id)
        reply_port = context.metadata.custom.get("reply_port", context.sender.port)
        reply_target = NodeInfo(node_id=context.sender.node_id, host=context.sender.host, port=reply_port)
        
        await self.service.bus.send(
            reply_target,
            MessageType.MEMBER_SNAPSHOT_RESP,
            {"snapshot": self.service.get_snapshot()},
            reply_meta
        )


class _SnapshotResponseHandler(MessageHandler):
    """Applies incoming responses for manual synchronization."""

    def __init__(self, service: ClusterMembershipService) -> None:
        self.service = service

    async def handle(self, context: MessageContext) -> None:
        snapshot = context.payload.get("snapshot", [])
        await self.service.sync_snapshot(snapshot)
