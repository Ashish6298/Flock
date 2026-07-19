"""Serializer interface protocol."""

from typing import Protocol, Any

class Serializer(Protocol):
    """Protocol defining serialization and deserialization of network messages/payloads."""

    def serialize(self, data: Any) -> bytes:
        """Serialize data to bytes.

        Raises:
            SerializationError: If serialization fails.
        """
        ...

    def deserialize(self, data: bytes) -> Any:
        """Deserialize bytes back into structured data.

        Raises:
            SerializationError: If deserialization fails.
        """
        ...
