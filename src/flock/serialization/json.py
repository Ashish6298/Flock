"""JSON Serializer implementation for Flock."""

import json
from typing import Any
from flock.exceptions import SerializationError

class JsonSerializer:
    """Serializer implementation that encodes and decodes JSON structures."""

    def serialize(self, data: Any) -> bytes:
        """Serialize Python structures to UTF-8 JSON bytes."""
        try:
            return json.dumps(data).encode("utf-8")
        except (TypeError, ValueError) as err:
            raise SerializationError(f"Failed to serialize data to JSON: {err}") from err

    def deserialize(self, data: bytes) -> Any:
        """Deserialize UTF-8 JSON bytes back to Python structures."""
        try:
            return json.loads(data.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as err:
            raise SerializationError(f"Failed to deserialize JSON data: {err}") from err
