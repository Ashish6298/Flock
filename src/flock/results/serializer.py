"""Serialization pipelines managing JSON/Msgpack and payload checksum generation."""

import json
import hashlib
import msgpack
from typing import Any, Optional
from flock.results.exceptions import ResultSerializationError

class ResultSerializer:
    """Manages json and msgpack payload transformations and integrity hashing checks."""

    def __init__(self, default_format: str = "json") -> None:
        self.default_format = default_format

    def serialize(self, value: Any, format_name: Optional[str] = None) -> bytes:
        """Encode value into binary payload.

        Raises:
            ResultSerializationError: On encoding failure.
        """
        fmt = format_name or self.default_format
        try:
            if fmt == "json":
                return json.dumps(value).encode("utf-8")
            elif fmt == "msgpack":
                return bytes(msgpack.packb(value))
            else:
                raise ResultSerializationError(f"Unsupported serializer format: {fmt}")
        except Exception as err:
            raise ResultSerializationError(f"Failed to serialize result value: {err}") from err

    def deserialize(self, payload: bytes, format_name: str = "json") -> Any:
        """Decode value from binary payload.

        Raises:
            ResultSerializationError: On decoding failure.
        """
        try:
            if format_name == "json":
                return json.loads(payload.decode("utf-8"))
            elif format_name == "msgpack":
                return msgpack.unpackb(payload)
            else:
                raise ResultSerializationError(f"Unsupported deserializer format: {format_name}")
        except Exception as err:
            raise ResultSerializationError(f"Failed to deserialize result payload: {err}") from err

    def generate_checksum(self, payload: bytes) -> str:
        """Calculate SHA256 checksum."""
        return hashlib.sha256(payload).hexdigest()
