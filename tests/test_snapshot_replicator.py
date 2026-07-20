"""Unit tests for SnapshotReplicator."""

import asyncio
import json
import time
from unittest.mock import AsyncMock, MagicMock
import pytest
from flock.events.bus import EventBus
from flock.messaging.bus import MessageBus
from flock.snapshot.models import SnapshotMetadata
from flock.snapshot.replicator import SnapshotReplicator
from flock.types import NodeInfo


@pytest.mark.asyncio
async def test_replicator_chunking_and_transmission() -> None:
    events = EventBus()
    bus = MagicMock(spec=MessageBus)
    bus.send = AsyncMock()

    # Small chunk size for testing: 10 bytes
    replicator = SnapshotReplicator("node-1", bus, events, chunk_size_bytes=10)

    data = b"abcdefghijklmnopqrstuvwxyz"  # 26 bytes -> 3 chunks
    checksum = "7e002ba815ced67475bc2e2a8747a06940a6b7d2f9ef0b0460a8b9fdfb744007"
    
    metadata = SnapshotMetadata(
        snapshot_id="snap-1",
        applied_index=1,
        current_term=1,
        timestamp=time.time(),
        checksum=checksum,
        size_bytes=len(data),
    )

    # Verify chunk_snapshot partition logic
    manifest = replicator.chunk_snapshot(metadata, data)
    assert manifest.total_chunks == 3
    assert manifest.chunk_size_bytes == 10

    peer = NodeInfo(node_id="peer-1", host="127.0.0.1", port=9000)
    await replicator.send_snapshot(peer, metadata, data)

    # 3 chunk sends + 1 completed send = 4 sends
    assert bus.send.call_count == 4
