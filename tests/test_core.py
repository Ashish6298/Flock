"""Tests verifying the foundational core elements of Flock."""

import pytest
from flock.config import ClusterConfig
from flock.types import TaskSpec, TaskStatus
from flock.exceptions import FlockError

def test_exceptions_hierarchy() -> None:
    """Verify exceptions subclass FlockError."""
    from flock.exceptions import TransportError, SerializationError
    assert issubclass(TransportError, FlockError)
    assert issubclass(SerializationError, FlockError)

def test_task_spec_creation() -> None:
    """Verify task spec creates unique task IDs."""
    spec1 = TaskSpec.create("test_task", 1, 2, val="abc")
    spec2 = TaskSpec.create("test_task", 1, 2, val="abc")
    
    assert spec1.task_id != spec2.task_id
    assert spec1.name == "test_task"
    assert spec1.args == (1, 2)
    assert spec1.kwargs == {"val": "abc"}

def test_pydantic_configuration() -> None:
    """Verify cluster config parses and validates input correctly."""
    cfg = ClusterConfig(node_id="node-123", metadata={"role": "worker"})
    assert cfg.node_id == "node-123"
    assert cfg.transport.port == 8000
    assert cfg.metadata["role"] == "worker"
