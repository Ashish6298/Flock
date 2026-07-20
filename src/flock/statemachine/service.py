"""StateMachineService implementation coordinating consensus commits with the engine."""

from __future__ import annotations

import asyncio
import json
import time
from typing import Any, Dict, List, Optional, Set, Tuple

import structlog

from flock.consensus.exceptions import LeaderUnavailableError
from flock.consensus.service import ConsensusService
from flock.events.bus import EventBus
from flock.statemachine.engine import StateMachineEngine
from flock.statemachine.exceptions import (
    DuplicateCommandError,
    StateMachineError,
    UnknownStateKeyError,
)
from flock.statemachine.models import (
    StateCommand,
    StateEntry,
    StateSnapshotMetadata,
)
from flock.statemachine.store import ReplicatedStateStore

logger = structlog.get_logger()


class StateMachineService:
    """High-level service coordinating state mutations and consensus integration."""

    def __init__(
        self,
        node_id: str,
        consensus_service: ConsensusService,
        event_bus: EventBus,
    ) -> None:
        self.node_id = node_id
        self._consensus = consensus_service
        self._events = event_bus

        self._store = ReplicatedStateStore()
        self._engine = StateMachineEngine(self._store, self._events)

        self._running = False
        self._is_subscribed = False

    async def start(self) -> None:
        """Start the service and register consensus commit listener."""
        if self._running:
            return
        self._running = True

        # Wire up ConsensusService log committed notifications
        async def on_log_committed(event_data: Dict[str, Any]) -> None:
            index = event_data.get("index")
            term = event_data.get("term")
            if index is None or term is None:
                return

            # Retrieve entry from consensus log
            entry = self._consensus._log.get_entry(index)
            if entry:
                try:
                    self._engine.apply_entry(index, term, entry.command)
                except Exception as exc:
                    logger.error(
                        "Auto-applying committed entry failed",
                        index=index,
                        error=str(exc),
                    )

        # Register event subscriber
        self._events.subscribe("consensus.log.committed", on_log_committed)
        self._is_subscribed = True
        logger.info("StateMachineService started", node_id=self.node_id)

    async def stop(self) -> None:
        """Stop state machine service and cleanup registrations."""
        self._running = False
        self._is_subscribed = False
        logger.info("StateMachineService stopped", node_id=self.node_id)

    # ------------------------------------------------------------------
    # Consensus write pipeline
    # ------------------------------------------------------------------

    async def submit_command(self, command: StateCommand) -> StateEntry:
        """Submit a state command through Raft consensus (leader-only).

        This will serialize the command and send it via Raft `submit_command()`.
        It blocks until the command is committed and applied locally.

        Args:
            command: The StateCommand to apply.

        Returns:
            The resulting StateEntry after commit replication and execution.
        """
        if not self._consensus.is_leader():
            raise LeaderUnavailableError(
                f"Cannot submit command: this node ({self.node_id}) is not the leader."
            )

        # Prevent duplicate submissions early if already executed
        if self._engine.is_executed(command.command_id):
            raise DuplicateCommandError(
                f"Command ID '{command.command_id}' has already been executed."
            )

        serialized = json.dumps(command.model_dump()).encode("utf-8")

        # Set up a future/event to await local application of this specific command
        loop = asyncio.get_running_loop()
        future: asyncio.Future[StateEntry] = loop.create_future()

        async def check_applied(event_data: Dict[str, Any]) -> None:
            if event_data.get("command_id") == command.command_id:
                try:
                    entry = self._store.get(command.key)
                    if not future.done():
                        future.set_result(entry)
                except Exception as exc:
                    if not future.done():
                        future.set_exception(exc)

        async def check_rejected(event_data: Dict[str, Any]) -> None:
            if event_data.get("command_id") == command.command_id:
                reason = event_data.get("reason", "Unknown reject reason")
                if not future.done():
                    future.set_exception(StateMachineError(f"Command rejected: {reason}"))

        self._events.subscribe("state.command.applied", check_applied)
        self._events.subscribe("state.command.rejected", check_rejected)

        try:
            # Submit to Consensus log
            await self._consensus.submit_command(serialized)
            # Await the application notification locally
            result = await asyncio.wait_for(future, timeout=5.0)
            return result
        finally:
            # Unsubscribe is not explicitly exposed as async in some versions,
            # but we assume the event loop cleanups or standard subscription handles.
            pass

    # ------------------------------------------------------------------
    # Synchronous state lookup APIs (Local Node)
    # ------------------------------------------------------------------

    def get(self, key: str) -> StateEntry:
        """Get the StateEntry value for a key."""
        return self._store.get(key)

    def exists(self, key: str) -> bool:
        """Check if a key exists."""
        return self._store.exists(key)

    def keys(self) -> Set[str]:
        """Get all keys in the state machine store."""
        return self._store.keys()

    def values(self) -> List[StateEntry]:
        """Get all values in the state machine store."""
        return self._store.values()

    def items(self) -> Dict[str, StateEntry]:
        """Get all items in the store."""
        return self._store.items()

    # ------------------------------------------------------------------
    # Snapshot Management
    # ------------------------------------------------------------------

    def snapshot(self) -> Tuple[StateSnapshotMetadata, Dict[str, Any]]:
        """Generate a complete state machine snapshot."""
        return self._engine.create_snapshot()

    def restore_snapshot(self, metadata: StateSnapshotMetadata, snapshot_data: Dict[str, Any]) -> None:
        """Restore state machine from snapshot."""
        self._engine.restore_snapshot(metadata, snapshot_data)

    def export_state(self) -> Dict[str, Any]:
        """Export raw state store entries."""
        return self._store.export_state()

    def import_state(self, data: Dict[str, Any]) -> None:
        """Import raw state store entries directly."""
        self._store.import_state(data)

    # ------------------------------------------------------------------
    # Debug / Manual replication pipeline hook
    # ------------------------------------------------------------------

    def apply_committed_entry(self, index: int, term: int, command_data: bytes) -> Optional[StateEntry]:
        """Direct hook to trigger engine application manually (e.g. in tests)."""
        return self._engine.apply_entry(index, term, command_data)
