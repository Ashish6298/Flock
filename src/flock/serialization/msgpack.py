"""MessagePack Serializer implementation for Flock."""

from typing import Any
from flock.exceptions import SerializationError

try:
    import msgpack
    HAS_MSGPACK = True
except ImportError:
    HAS_MSGPACK = False

class MsgpackSerializer:
    """Serializer implementation using MessagePack."""

    def __init__(self) -> None:
        if not HAS_MSGPACK:
            raise RuntimeError("msgpack package is required to use MsgpackSerializer")

    def serialize(self, data: Any) -> bytes:
        """Serialize data to MessagePack bytes."""
        try:
            val = msgpack.packb(data)
            if not isinstance(val, bytes):
                raise SerializationError("Serialized value is not bytes")
            return val
        except Exception as err:
            raise SerializationError(f"Failed to serialize msgpack data: {err}") from err

    def deserialize(self, data: bytes) -> Any:
        """Deserialize MessagePack bytes."""
        try:
            return msgpack.unpackb(data)
        except Exception as err:
            raise SerializationError(f"Failed to deserialize msgpack data: {err}") from err
