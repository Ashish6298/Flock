"""Replicated State Store implementation."""

from __future__ import annotations

import copy
import hashlib
import json
import threading
from typing import Any, Dict, List, Optional, Set, Tuple, cast

from flock.statemachine.exceptions import (
    CommandValidationError,
    StateConflictError,
    UnknownStateKeyError,
)
from flock.statemachine.models import StateCommand, StateEntry, StateOperation


class ReplicatedStateStore:
    """Thread-safe in-memory state engine applying commands deterministically."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._state: Dict[str, StateEntry] = {}

    def get(self, key: str) -> StateEntry:
        """Retrieve the state entry for a key.

        Args:
            key: The state key.

        Returns:
            The associated StateEntry.

        Raises:
            UnknownStateKeyError: If key does not exist.
        """
        with self._lock:
            if key not in self._state:
                raise UnknownStateKeyError(f"Key '{key}' not found in state store.")
            return self._state[key]

    def exists(self, key: str) -> bool:
        """Check if a key exists."""
        with self._lock:
            return key in self._state

    def keys(self) -> Set[str]:
        """Get all keys in the store."""
        with self._lock:
            return set(self._state.keys())

    def values(self) -> List[StateEntry]:
        """Get all values in the store."""
        with self._lock:
            return list(self._state.values())

    def items(self) -> Dict[str, StateEntry]:
        """Get copy of all items."""
        with self._lock:
            return dict(self._state)

    def apply(self, command: StateCommand, term: int, index: int) -> StateEntry:
        """Apply a command to the store deterministically.

        Args:
            command: The StateCommand to apply.
            term: The term of the Raft log entry.
            index: The index of the Raft log entry.

        Returns:
            The newly created or updated StateEntry.
        """
        with self._lock:
            op = command.operation
            key = command.key
            val = command.value
            ts = command.timestamp

            # Retrieve existing entry if present
            existing = self._state.get(key)
            new_version = (existing.version + 1) if existing else 1

            if op == StateOperation.PUT:
                entry = StateEntry(value=val, version=new_version, term=term, index=index, timestamp=ts)
                self._state[key] = entry
                return entry

            elif op == StateOperation.UPDATE:
                if not existing:
                    raise StateConflictError(f"Cannot update non-existent key '{key}'.")
                entry = StateEntry(value=val, version=new_version, term=term, index=index, timestamp=ts)
                self._state[key] = entry
                return entry

            elif op == StateOperation.DELETE:
                if not existing:
                    raise StateConflictError(f"Cannot delete non-existent key '{key}'.")
                del self._state[key]
                return existing

            elif op == StateOperation.UPSERT:
                entry = StateEntry(value=val, version=new_version, term=term, index=index, timestamp=ts)
                self._state[key] = entry
                return entry

            elif op == StateOperation.INCREMENT:
                curr_numeric = existing.value if existing else 0
                if not isinstance(curr_numeric, (int, float)):
                    raise CommandValidationError(f"Cannot increment non-numeric value of type {type(curr_numeric)}.")
                incr_by = val if val is not None else 1
                if not isinstance(incr_by, (int, float)):
                    raise CommandValidationError(f"Increment delta must be numeric.")
                new_val = curr_numeric + incr_by
                entry = StateEntry(value=new_val, version=new_version, term=term, index=index, timestamp=ts)
                self._state[key] = entry
                return entry

            elif op == StateOperation.APPEND:
                curr_list = existing.value if existing else []
                if not isinstance(curr_list, list):
                    raise CommandValidationError(f"Cannot append to non-list value of type {type(curr_list)}.")
                new_list = list(curr_list)
                new_list.append(val)
                entry = StateEntry(value=new_list, version=new_version, term=term, index=index, timestamp=ts)
                self._state[key] = entry
                return entry

            elif op == StateOperation.SET_ADD:
                curr_set_list = existing.value if existing else []
                if not isinstance(curr_set_list, list):
                    raise CommandValidationError(f"Cannot set_add on non-list value of type {type(curr_set_list)}.")
                new_set_list = list(curr_set_list)
                if val not in new_set_list:
                    new_set_list.append(val)
                entry = StateEntry(value=new_set_list, version=new_version, term=term, index=index, timestamp=ts)
                self._state[key] = entry
                return entry

            elif op == StateOperation.SET_REMOVE:
                curr_rem_list = existing.value if existing else []
                if not isinstance(curr_rem_list, list):
                    raise CommandValidationError(f"Cannot set_remove on non-list value of type {type(curr_rem_list)}.")
                new_rem_list = list(curr_rem_list)
                if val in new_rem_list:
                    new_rem_list.remove(val)
                entry = StateEntry(value=new_rem_list, version=new_version, term=term, index=index, timestamp=ts)
                self._state[key] = entry
                return entry

            elif op == StateOperation.MAP_PUT:
                curr_map = existing.value if existing else {}
                if not isinstance(curr_map, dict):
                    raise CommandValidationError(f"Cannot map_put on non-dict value of type {type(curr_map)}.")
                if not isinstance(val, dict):
                    raise CommandValidationError("MAP_PUT value must be a dictionary.")
                new_map = dict(curr_map)
                new_map.update(val)
                entry = StateEntry(value=new_map, version=new_version, term=term, index=index, timestamp=ts)
                self._state[key] = entry
                return entry

            elif op == StateOperation.MAP_DELETE:
                curr_del_map = existing.value if existing else {}
                if not isinstance(curr_del_map, dict):
                    raise CommandValidationError(f"Cannot map_delete on non-dict value of type {type(curr_del_map)}.")
                new_del_map = dict(curr_del_map)
                if val in new_del_map:
                    del new_del_map[val]
                entry = StateEntry(value=new_del_map, version=new_version, term=term, index=index, timestamp=ts)
                self._state[key] = entry
                return entry

            else:
                raise CommandValidationError(f"Unsupported operation type: {op}")

    def export_state(self) -> Dict[str, Any]:
        """Export raw state for snapshot serialization."""
        with self._lock:
            # Create a clean serializable dictionary representation
            data = {}
            for k, entry in self._state.items():
                data[k] = entry.model_dump()
            return data

    def import_state(self, data: Dict[str, Any]) -> None:
        """Import raw state replacing existing entries completely."""
        with self._lock:
            new_state = {}
            for k, raw_entry in data.items():
                new_state[k] = StateEntry(**raw_entry)
            self._state = new_state

    def generate_checksum(self) -> str:
        """Generate a stable SHA256 checksum of the current state contents."""
        with self._lock:
            # Sort keys to ensure deterministic checksum
            sorted_keys = sorted(self._state.keys())
            serialized = []
            for k in sorted_keys:
                entry = self._state[k]
                serialized.append(f"{k}:{entry.version}:{entry.index}:{entry.term}:{json.dumps(entry.value, sort_keys=True)}")
            hash_str = "|".join(serialized)
            return hashlib.sha256(hash_str.encode("utf-8")).hexdigest()

    def clear(self) -> None:
        """Clear the store completely."""
        with self._lock:
            self._state.clear()
