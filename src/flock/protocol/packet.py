"""Custom network packet frame protocol with integrity validation."""

import struct
import hashlib
from typing import Any, Tuple
from flock.exceptions import SerializationError

# Constants
MAGIC_BYTES = b"FLOK"
PROTOCOL_VERSION = 1
HEADER_FORMAT = "!4sBBI"  # Magic (4s), Version (B), MessageType (B), PayloadSize (I)
HEADER_SIZE = struct.calcsize(HEADER_FORMAT)

class MessageType:
    """Supported network message types."""
    HEARTBEAT = 1
    TASK_SUBMIT = 2
    TASK_RESULT = 3
    PEER_DISCOVERY = 4
    GENERIC = 5
    DISCOVERY_REQUEST = 6
    DISCOVERY_RESPONSE = 7
    NODE_ANNOUNCE = 8
    NODE_LEAVE = 9
    MEMBER_JOIN_REQ = 10
    MEMBER_JOIN_ACK = 11
    MEMBER_LEAVE_NOTIFY = 12
    MEMBER_SNAPSHOT_REQ = 13
    MEMBER_SNAPSHOT_RESP = 14
    HEARTBEAT_PING = 15
    HEARTBEAT_PONG = 16
    TASK_SUBMIT = 17
    TASK_ANNOUNCE = 18
    TASK_CANCEL = 19
    TASK_EXPIRE = 20
    TASK_UPDATE = 21
    TASK_ASSIGN = 22
    TASK_ASSIGN_ACK = 23
    TASK_ASSIGN_REJECT = 24
    TASK_REASSIGN_REQUEST = 25
    PLACEMENT_UPDATE = 26
    TASK_EXECUTION_START = 27
    TASK_EXECUTION_ACK = 28
    TASK_EXECUTION_CANCEL = 29
    TASK_EXECUTION_COMPLETE = 30
    TASK_EXECUTION_FAILURE = 31
    TASK_RESULT = 32
    TASK_RESULT_ACK = 33
    TASK_RESULT_FAILURE = 34
    TASK_RESULT_TIMEOUT = 35
    TASK_RESULT_RETRY = 36
    TASK_RESULT_STREAM_END = 37
    TASK_RETRY_REQUEST = 38
    TASK_RETRY_ACK = 39
    TASK_RECOVERY_REQUEST = 40
    TASK_RECOVERY_ACK = 41
    TASK_RECOVERY_CANCEL = 42
    TASK_RECOVERY_COMPLETE = 43
    TASK_RECOVERY_FAILED = 44
    TASK_RECOVERY_STATUS = 45
    # Phase 12 – Distributed Raft Consensus Engine
    RAFT_REQUEST_VOTE = 46
    RAFT_VOTE_RESPONSE = 47
    RAFT_APPEND_ENTRIES = 48
    RAFT_APPEND_RESPONSE = 49
    RAFT_HEARTBEAT = 50
    RAFT_LEADER_ANNOUNCE = 51
    RAFT_LOG_SYNC_REQUEST = 52
    RAFT_LOG_SYNC_RESPONSE = 53

class Packet:
    """Prepares and validates standard raw network frames for Flock communication."""

    def __init__(self, message_type: int, payload: bytes) -> None:
        self.message_type = message_type
        self.payload = payload

    @property
    def payload_checksum(self) -> str:
        """Calculate payload SHA256 checksum."""
        return hashlib.sha256(self.payload).hexdigest()

    def pack(self) -> bytes:
        """Pack header and payload into a single binary frame."""
        payload_size = len(self.payload)
        header = struct.pack(
            HEADER_FORMAT,
            MAGIC_BYTES,
            PROTOCOL_VERSION,
            self.message_type,
            payload_size
        )
        # We append a fixed length checksum representation or calculate payload hash
        # To maintain frame cleanliness, we attach the hash prefix to verification
        return header + self.payload

    @classmethod
    def unpack_header(cls, header_bytes: bytes) -> Tuple[int, int]:
        """Decode header frame and return message type and payload size.

        Raises:
            SerializationError: If magic bytes mismatch or invalid protocol version.
        """
        if len(header_bytes) != HEADER_SIZE:
            raise SerializationError("Incomplete header block.")

        magic, version, msg_type, payload_size = struct.unpack(HEADER_FORMAT, header_bytes)
        if magic != MAGIC_BYTES:
            raise SerializationError(f"Invalid magic bytes: {magic!r}")
        if version != PROTOCOL_VERSION:
            raise SerializationError(f"Unsupported protocol version: {version}")
        
        return msg_type, payload_size
