"""SnapshotService orchestrating log compaction and consensus state replication."""

from __future__ import annotations

import asyncio
import json
import time
from typing import Any, Dict, List, Optional

import structlog

from flock.cluster.registry import MembershipRegistry
from flock.consensus.service import ConsensusService
from flock.events.bus import EventBus
from flock.messaging.bus import MessageBus
from flock.messaging.handlers import MessageHandler
from flock.messaging.models import MessageContext, MessageMetadata
from flock.protocol.packet import MessageType
from flock.snapshot.compactor import LogCompactor
from flock.snapshot.exceptions import SnapshotError, SnapshotRestoreError
from flock.snapshot.handlers import (
    _ChunkHandler,
    _InstallRequestHandler,
    _TransferCompleteHandler,
)
from flock.snapshot.models import (
    SnapshotChunk,
    SnapshotInstallRequest,
    SnapshotInstallResponse,
    SnapshotMetadata,
)
from flock.snapshot.replicator import SnapshotReplicator
from flock.snapshot.storage import SnapshotStorage
from flock.statemachine.service import StateMachineService
from flock.types import NodeInfo

logger = structlog.get_logger()


class SnapshotService:
    """Orchestrates automatic snapshot triggers, replication, and log compaction."""

    def __init__(
        self,
        node_id: str,
        consensus_service: ConsensusService,
        state_machine_service: StateMachineService,
        message_bus: MessageBus,
        event_bus: EventBus,
        membership_registry: MembershipRegistry,
        commit_threshold: int = 10,
    ) -> None:
        self.node_id = node_id
        self._consensus = consensus_service
        self._fsm = state_machine_service
        self._bus = message_bus
        self._events = event_bus
        self._membership = membership_registry
        self.commit_threshold = commit_threshold

        self.storage = SnapshotStorage()
        self.compactor = LogCompactor(self._consensus._log)
        self.replicator = SnapshotReplicator(node_id, self._bus, self._events)

        self._running = False
        self._is_subscribed = False

    async def start(self) -> None:
        """Start snapshot manager and listen for log committed signals."""
        if self._running:
            return
        self._running = True

        async def on_log_committed(event_data: Dict[str, Any]) -> None:
            index = event_data.get("index", 0)
            # Trigger snapshot creation automatically if log index modulo commit_threshold is 0
            if index > 0 and index % self.commit_threshold == 0:
                try:
                    await self.create_snapshot()
                except Exception as exc:
                    logger.error("Failed to automatically generate snapshot", index=index, error=str(exc))

        self._events.subscribe("consensus.log.committed", on_log_committed)
        self._is_subscribed = True

        self._register_handlers()
        logger.info("SnapshotService started", node_id=self.node_id)

    async def stop(self) -> None:
        """Stop SnapshotService execution."""
        self._running = False
        self._is_subscribed = False
        logger.info("SnapshotService stopped", node_id=self.node_id)

    async def create_snapshot(self) -> SnapshotMetadata:
        """Export current FSM state, save snapshot, and compact consensus log.

        Returns:
            The created SnapshotMetadata.
        """
        try:
            # 1. Generate snapshot from replicated state machine
            fsm_metadata, snapshot_data = self._fsm.snapshot()
            
            # Serialize snapshot contents
            data_bytes = json.dumps(snapshot_data).encode("utf-8")
            size_bytes = len(data_bytes)

            metadata = SnapshotMetadata(
                snapshot_id=fsm_metadata.checksum[:16],
                applied_index=fsm_metadata.applied_index,
                current_term=fsm_metadata.current_term,
                timestamp=fsm_metadata.timestamp,
                checksum=fsm_metadata.checksum,
                size_bytes=size_bytes,
            )

            # 2. Save snapshot inside local SnapshotStorage
            self.storage.save_snapshot(metadata, data_bytes)
            
            await self._events.publish(
                "snapshot.created",
                {"snapshot_id": metadata.snapshot_id, "applied_index": metadata.applied_index},
            )

            # 3. Compact log up to index
            await self._events.publish(
                "snapshot.compaction.started",
                {"last_included_index": metadata.applied_index},
            )
            
            self.compactor.compact(metadata.applied_index, metadata.current_term)
            
            await self._events.publish(
                "snapshot.compaction.completed",
                {"last_included_index": metadata.applied_index},
            )

            return metadata

        except Exception as exc:
            await self._events.publish(
                "snapshot.creation.failed",
                {"error": str(exc)},
            )
            raise SnapshotError(f"Snapshot creation failed: {exc}") from exc

    async def install_snapshot_on_peer(self, peer: NodeInfo, snapshot_id: str) -> None:
        """Send InstallSnapshot RPC request and stream snapshot chunks.

        Args:
            peer: Remote destination NodeInfo.
            snapshot_id: Target snapshot identifier.
        """
        snapshot_tuple = self.storage.get_snapshot(snapshot_id)
        if not snapshot_tuple:
            raise SnapshotError(f"Snapshot {snapshot_id} not found in storage.")

        metadata, data_bytes = snapshot_tuple
        manifest = self.replicator.chunk_snapshot(metadata, data_bytes)

        install_req = SnapshotInstallRequest(
            leader_id=self.node_id,
            term=self._consensus.get_current_term(),
            last_included_index=metadata.applied_index,
            last_included_term=metadata.current_term,
            metadata=metadata,
            manifest=manifest,
        )

        payload = install_req.model_dump()
        
        # Send installation header
        await self._bus.send(
            peer,
            MessageType.SNAPSHOT_INSTALL_REQUEST,
            payload,
        )

        # Stream chunks incrementally
        await self.replicator.send_snapshot(peer, metadata, data_bytes)

    # ------------------------------------------------------------------
    # Handlers wiring
    # ------------------------------------------------------------------

    def _register_handlers(self) -> None:
        """Register snapshot network message handlers."""
        router = self._bus.router
        router.register(
            MessageType.SNAPSHOT_INSTALL_REQUEST,
            _InstallRequestHandler(self),
        )
        router.register(
            MessageType.SNAPSHOT_CHUNK,
            _ChunkHandler(self),
        )
        router.register(
            MessageType.SNAPSHOT_TRANSFER_COMPLETE,
            _TransferCompleteHandler(self),
        )
