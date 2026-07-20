"""High-level StorageService coordinating WAL logs and startup recovery."""

from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Optional

import structlog

from flock.cluster.registry import MembershipRegistry
from flock.consensus.service import ConsensusService
from flock.events.bus import EventBus
from flock.messaging.bus import MessageBus
from flock.protocol.packet import MessageType
from flock.snapshot.storage import SnapshotStorage
from flock.storage.backend import FileStorageBackend
from flock.storage.engine import PersistentStorageEngine
from flock.storage.exceptions import StorageError
from flock.storage.models import (
    StorageConfiguration,
    StorageHealthReport,
    StorageMetadata,
    WALReplayResult,
)
from flock.storage.recovery import RecoveryEngine
from flock.statemachine.service import StateMachineService

logger = structlog.get_logger()


class StorageService:
    """Wire WAL persistence, trigger checkpoints, and coordinate crash recovery."""

    def __init__(
        self,
        node_id: str,
        consensus_service: ConsensusService,
        state_machine_service: StateMachineService,
        snapshot_storage: SnapshotStorage,
        message_bus: MessageBus,
        event_bus: EventBus,
        config: StorageConfiguration,
    ) -> None:
        self.node_id = node_id
        self._consensus = consensus_service
        self._fsm = state_machine_service
        self._snap_store = snapshot_storage
        self._bus = message_bus
        self._events = event_bus
        self._config = config

        # File IO backend
        self.backend = FileStorageBackend(config.data_directory)
        self.engine = PersistentStorageEngine(self.backend, config)
        self.recovery_engine = RecoveryEngine(self.engine, self._fsm, self._snap_store)

        self._running = False
        self._is_subscribed = False

    async def start(self) -> None:
        """Start the storage manager service.

        Subscribes to EventBus 'state.command.applied' triggers to dynamically append to Write-Ahead Log.
        """
        if self._running:
            return
        self._running = True

        async def on_command_applied(event_data: Dict[str, Any]) -> None:
            # When FSM applies a command, save to WAL dynamically
            command_id = event_data.get("command_id")
            key = event_data.get("key")
            index = event_data.get("index")
            term = event_data.get("term")

            if not command_id or index is None or term is None:
                return

            try:
                # Retrieve command bytes representation
                # Find inside consensus log
                entry = self._consensus._log.get_entry(index)
                if entry:
                    # Append transaction block to WAL
                    self.engine.wal.append(index, term, command_id, entry.command)
                    
                    # Fire entry appended event
                    await self._events.publish(
                        "wal.entry.appended",
                        {"index": index, "command_id": command_id},
                    )
            except Exception as exc:
                logger.error("Failed to append entry to WAL", index=index, error=str(exc))

        self._events.subscribe("state.command.applied", on_command_applied)
        self._is_subscribed = True

        self._register_handlers()
        logger.info("StorageService started", node_id=self.node_id)

    async def stop(self) -> None:
        """Stop storage service operations."""
        self._running = False
        self._is_subscribed = False
        logger.info("StorageService stopped", node_id=self.node_id)

    def recover(self) -> WALReplayResult:
        """Replay log files on node bootstrap."""
        return self.recovery_engine.recover_node_state()

    def get_health_report(self) -> StorageHealthReport:
        """Expose storage integrity and stats metrics."""
        try:
            stats = self.engine.get_statistics()
            return StorageHealthReport(
                is_healthy=True,
                total_segments=stats.segment_count,
            )
        except Exception as exc:
            return StorageHealthReport(
                is_healthy=False,
                total_segments=0,
                error_message=str(exc),
            )

    # ------------------------------------------------------------------
    # Network Handlers
    # ------------------------------------------------------------------

    def _register_handlers(self) -> None:
        """Register storage health query endpoints."""
        router = self._bus.router
        
        async def handle_health_query(context: Any) -> None:
            report = self.get_health_report()
            reply_target = context.sender
            await self._bus.send(
                reply_target,
                MessageType.STORAGE_HEALTH_RESPONSE,
                report.model_dump(),
            )

        router.register(
            MessageType.STORAGE_HEALTH_REQUEST,
            # Wrap standard coroutine into MessageHandler structure dynamically if needed
            # For simplicity, wrap it in a helper class conforming to MessageHandler
            _HealthQueryHandler(handle_health_query),
        )


from flock.messaging.handlers import MessageHandler

class _HealthQueryHandler(MessageHandler):
    def __init__(self, callback: Any) -> None:
        self.callback = callback

    async def handle(self, context: Any) -> None:
        await self.callback(context)
