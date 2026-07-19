"""Unit tests for Serialization encoders."""

import pytest
from flock.serialization.json import JsonSerializer
from flock.exceptions import SerializationError

def test_json_serialization_roundtrip() -> None:
    """Verify JSON serializes and deserializes payloads correctly."""
    serializer = JsonSerializer()
    data = {"key": "value", "list": [1, 2, 3], "nested": {"a": True}}
    
    serialized = serializer.serialize(data)
    deserialized = serializer.deserialize(serialized)
    
    assert deserialized == data

def test_json_serialization_failure() -> None:
    """Verify serialization fails on non-serializable objects (like sets or classes)."""
    serializer = JsonSerializer()
    with pytest.raises(SerializationError):
        serializer.serialize({1, 2, 3})
