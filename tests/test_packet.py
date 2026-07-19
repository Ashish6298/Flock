"""Unit tests for packet protocol framing."""

import pytest
from flock.protocol.packet import Packet, MessageType
from flock.exceptions import SerializationError

def test_packet_pack_unpack() -> None:
    """Verify that packing and unpacking header returns original type and payload size."""
    from flock.protocol.packet import HEADER_SIZE
    payload = b"hello world payload"
    pkt = Packet(message_type=MessageType.HEARTBEAT, payload=payload)
    
    packed = pkt.pack()
    # Unpack header from front
    header_bytes = packed[:HEADER_SIZE]
    msg_type, size = Packet.unpack_header(header_bytes)
    
    assert msg_type == MessageType.HEARTBEAT
    assert size == len(payload)
    assert packed[HEADER_SIZE:] == payload

def test_packet_checksum_validation() -> None:
    """Verify packet payload checksum generation."""
    pkt = Packet(message_type=MessageType.GENERIC, payload=b"abc")
    assert pkt.payload_checksum is not None

def test_packet_invalid_magic() -> None:
    """Verify pack validation fails with invalid magic bytes."""
    bad_header = b"BADK" + b"\x01\x01\x00\x00\x00\x05"
    with pytest.raises(SerializationError, match="Invalid magic bytes"):
        Packet.unpack_header(bad_header)
