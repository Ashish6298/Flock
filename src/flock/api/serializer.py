"""Response Serializer formatting JSON data."""

from __future__ import annotations

import json
from typing import Any

from flock.api.exceptions import SerializationError


class ResponseSerializer:
    """Formats response dictionaries into UTF-8 encoded bytes."""

    def __init__(self) -> None:
        pass

    def serialize(self, data: Any) -> bytes:
        """Encode arbitrary Python objects to bytes.

        Raises:
            SerializationError: If object is not serializable.
        """
        try:
            return json.dumps(data).encode("utf-8")
        except Exception as exc:
            raise SerializationError(f"Failed to serialize response: {exc}") from exc

    def deserialize(self, raw: bytes) -> Any:
        """Decode bytes back to Python objects.

        Raises:
            SerializationError: If JSON decoding fails.
        """
        try:
            return json.loads(raw.decode("utf-8"))
        except Exception as exc:
            raise SerializationError(f"Failed to deserialize request body: {exc}") from exc
