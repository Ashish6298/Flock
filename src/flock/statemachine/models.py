"""State Machine Models."""

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

class StateOperation(str, Enum):
    """Supported state machine operations."""
    PUT = "PUT"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    UPSERT = "UPSERT"
    INCREMENT = "INCREMENT"
    APPEND = "APPEND"
    SET_ADD = "SET_ADD"
    SET_REMOVE = "SET_REMOVE"
    MAP_PUT = "MAP_PUT"
    MAP_DELETE = "MAP_DELETE"

class StateCommand(BaseModel):
    """Represents a state machine transition command."""
    command_id: str
    operation: StateOperation
    key: str
    value: Any = None
    timestamp: float
    client_id: Optional[str] = None

    model_config = {
        "frozen": True
    }

class StateEntry(BaseModel):
    """Metadata and value metadata stored per key in the replicated store."""
    value: Any
    version: int
    term: int
    index: int
    timestamp: float

    model_config = {
        "frozen": True
    }

class StateSnapshotMetadata(BaseModel):
    """Metadata descriptor for state machine snapshots."""
    applied_index: int
    current_term: int
    version: int = 1
    timestamp: float
    checksum: str

    model_config = {
        "frozen": True
    }

class ReplicatedValue(BaseModel):
    """A wrapper model enclosing the key's state entry metadata and current value."""
    metadata: StateEntry
    value: Any

    model_config = {
        "frozen": True
    }
