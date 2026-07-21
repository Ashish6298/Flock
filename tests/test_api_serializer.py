"""Unit tests for ResponseSerializer."""

import pytest
from flock.api.exceptions import SerializationError
from flock.api.serializer import ResponseSerializer


def test_serializer_roundtrip() -> None:
    serializer = ResponseSerializer()
    data = {"status": "ok", "code": 200}

    raw = serializer.serialize(data)
    decoded = serializer.deserialize(raw)

    assert decoded == data


def test_deserialize_invalid_bytes_raises() -> None:
    serializer = ResponseSerializer()
    with pytest.raises(SerializationError):
        serializer.deserialize(b"invalid-json")
