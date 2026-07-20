"""StateMachineEngine implementation."""

from __future__ import annotations

import asyncio
import json
import logging
import threading
import time
from typing import Any, Dict, List, Optional, Set, Tuple

import structlog

from flock.events.bus import EventBus
from flock.statemachine.exceptions import (
    DuplicateCommandError,
    StateMachineError,
)
from flock.statemachine.models import (
    StateCommand,
    StateEntry,
    StateSnapshotMetadata,
)
from flock.statemachine.store import ReplicatedStateStore

logger = structlog.get_logger()


class StateMachineEngine:
    """Manages sequential command execution, idempotency, and log tracking."""

    def __init__(self, store: ReplicatedStateStore, event_bus: EventBus) -> None:
        self._store = store
        self._events = event_bus
        self._lock = threading.Lock()

        self._applied_index = 0
        self._current_term = 0

        # Idempotency cache: command_id -> timestamp (or True)
        self._executed_commands: Set[str] = set()

    @property
    def applied_index(self) -> int:
        """Get the highest applied log index."""
        with self._lock:
            return self._applied_index

    @property
    def current_term(self) -> int:
        """Get the current term from state machine perspective."""
        with self._lock:
            return self._current_term

    def is_executed(self, command_id: str) -> bool:
        """Check if a command has already been executed."""
        with self._lock:
            return command_id in self._executed_commands

    def apply_entry(self, index: int, term: int, command_data: bytes) -> Optional[StateEntry]:
        """Validate, deserialize, and apply a committed log entry atomically.

        Args:
            index: Raft index of the log entry.
            term: Raft term of the log entry.
            command_data: Serialized StateCommand bytes.

        Returns:
            The resulting StateEntry or None if skipped/already executed.
        """
        with self._lock:
            # 1. Enforce sequential application
            if index <= self._applied_index:
                logger.debug(
                    "Skipping already applied or stale index",
                    index=index,
                    applied_index=self._applied_index,
                )
                return None

            if index > self._applied_index + 1:
                # We can't apply out-of-order commits.
                raise StateMachineError(
                    f"Out of order commit index {index}. Current applied index is {self._applied_index}."
                )

            # 2. Parse StateCommand
            try:
                raw_dict = json.loads(command_data.decode("utf-8"))
                command = StateCommand(**raw_dict)
            except Exception as exc:
                self._publish_event(
                    "state.machine.error",
                    {"index": index, "term": term, "error": f"Deserialization error: {exc}"},
                )
                raise StateMachineError(f"Failed to deserialize StateCommand: {exc}") from exc

            # Publish command received event
            self._publish_event("state.command.received", {"command_id": command.command_id, "index": index, "term": term})

            # 3. Check idempotency
            if command.command_id in self._executed_commands:
                logger.info(
                    "Duplicate command ignored",
                    command_id=command.command_id,
                    index=index,
                )
                self._publish_event(
                    "state.command.rejected",
                    {
                        "command_id": command.command_id,
                        "reason": "Duplicate command ID",
                        "index": index,
                    },
                )
                # Still advance index so the log doesn't stall
                self._applied_index = index
                self._current_term = term
                return None

            # 4. Apply to state store
            try:
                entry = self._store.apply(command, term, index)

                # Record idempotency and index tracking
                self._executed_commands.add(command.command_id)
                self._applied_index = index
                self._current_term = term

                # Publish success events
                self._publish_event(
                    "state.command.applied",
                    {
                        "command_id": command.command_id,
                        "key": command.key,
                        "index": index,
                        "term": term,
                    },
                )
                self._publish_event(
                    "state.version.updated",
                    {
                        "key": command.key,
                        "version": entry.version,
                        "index": index,
                    },
                )
                return entry

            except Exception as exc:
                logger.error(
                    "Failed to apply command",
                    command_id=command.command_id,
                    error=str(exc),
                    index=index,
                )
                # Keep index advanced even if execution failed, so log doesn't block
                self._applied_index = index
                self._current_term = term

                self._publish_event(
                    "state.command.rejected",
                    {
                        "command_id": command.command_id,
                        "reason": str(exc),
                        "index": index,
                    },
                )
                self._publish_event(
                    "state.machine.error",
                    {"index": index, "term": term, "error": str(exc)},
                )
                raise StateMachineError(f"Apply failed: {exc}") from exc

    def _publish_event(self, event_type: str, data: Any) -> None:
        """Helper to fire events into the async EventBus."""
        try:
            loop = asyncio.get_running_loop()
            if loop.is_running():
                loop.create_task(self._events.publish(event_type, data))
        except RuntimeError:
            # Fallback if no loop is running (e.g. in synchronous tests)
            # Run it via a temporary/new loop or simply skip/print in sync context
            pass

    def create_snapshot(self) -> Tuple[StateSnapshotMetadata, Dict[str, Any]]:
        """Create an immutable state snapshot export.

        Returns:
            Tuple of (StateSnapshotMetadata, raw_state_dict).
        """
        with self._lock:
            state_data = self._store.export_state()
            checksum = self._store.generate_checksum()
            metadata = StateSnapshotMetadata(
                applied_index=self._applied_index,
                current_term=self._current_term,
                timestamp=time.time(),
                checksum=checksum,
            )
            # Record state command cache as well to preserve idempotency across restores
            snapshot_data = {
                "state": state_data,
                "executed_commands": list(self._executed_commands),
            }
            self._publish_event(
                "state.snapshot.created",
                {
                    "applied_index": self._applied_index,
                    "checksum": checksum,
                },
            )
            return metadata, snapshot_data

    def restore_snapshot(self, metadata: StateSnapshotMetadata, snapshot_data: Dict[str, Any]) -> None:
        """Restore state from snapshot data.

        Args:
            metadata: StateSnapshotMetadata describing the snapshot.
            snapshot_data: The snapshot contents.
        """
        with self._lock:
            # Re-verify checksum of imported state to guarantee safety
            self._store.import_state(snapshot_data["state"])
            current_checksum = self._store.generate_checksum()
            if current_checksum != metadata.checksum:
                # Rollback or raise error
                self._store.clear()
                raise StateMachineError(
                    f"Snapshot restoration failed: checksum mismatch. Expected {metadata.checksum}, calculated {current_checksum}."
                )

            self._executed_commands = set(snapshot_data.get("executed_commands", []))
            self._applied_index = metadata.applied_index
            self._current_term = metadata.current_term

            self._publish_event(
                "state.snapshot.restored",
                {
                    "applied_index": self._applied_index,
                    "checksum": current_checksum,
                },
            )

    def clear(self) -> None:
        """Clear store and engine tracking state."""
        with self._lock:
            self._store.clear()
            self._executed_commands.clear()
            self._applied_index = 0
            self._current_term = 0
