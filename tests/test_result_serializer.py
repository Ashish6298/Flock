"""Unit tests validating ResultSerializer JSON/Msgpack and checksum verify workflows."""

import pytest
from flock.results.serializer import ResultSerializer
from flock.results.exceptions import ResultSerializationError

def test_result_serializer_json_msgpack() -> None:
    serializer = ResultSerializer(default_format="json")
    val = {"status": "success", "count": 10}

    # JSON encoding
    payload_json = serializer.serialize(val)
    decoded_json = serializer.deserialize(payload_json, format_name="json")
    assert decoded_json == val

    # Msgpack encoding
    payload_msgpack = serializer.serialize(val, format_name="msgpack")
    decoded_msgpack = serializer.deserialize(payload_msgpack, format_name="msgpack")
    assert decoded_msgpack == val

    # Checksum verification
    chk = serializer.generate_checksum(payload_json)
    assert len(chk) == 64
    assert serializer.generate_checksum(payload_json) == chk
