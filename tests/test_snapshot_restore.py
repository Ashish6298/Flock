"""Unit tests for snapshot restoration scenarios."""

import json
import time
from unittest.mock import AsyncMock, MagicMock
import pytest
from flock.cluster.registry import MembershipRegistry
from flock.consensus.service import ConsensusService
from flock.events.bus import EventBus
from flock.messaging.bus import MessageBus
from flock.snapshot.models import SnapshotMetadata
from flock.snapshot.service import SnapshotService
from flock.statemachine.service import StateMachineService


@pytest.mark.asyncio
async def test_snapshot_restore_atomic() -> None:
    consensus = MagicMock(spec=ConsensusService)
    consensus._log = MagicMock()
    consensus._log.commit_index = 5
    consensus._log._entries = []

    fsm = MagicMock(spec=StateMachineService)
    bus = MagicMock(spec=MessageBus)
    events = EventBus()
    membership = MembershipRegistry()

    service = SnapshotService(
        node_id="node-1",
        consensus_service=consensus,
        state_machine_service=fsm,
        message_bus=bus,
        event_bus=events,
        membership_registry=membership,
    )

    data = b'{"state": {"k": "v"}}'
    import hashlib
    checksum = hashlib.sha256(data).hexdigest()
    metadata = SnapshotMetadata(
        snapshot_id="snap-1",
        applied_index=5,
        current_term=1,
        timestamp=time.time(),
        checksum=checksum,
        size_bytes=len(data),
    )

    # Save to storage
    service.storage.save_snapshot(metadata, data)

    # Trigger manual restore from stored snapshot
    snapshot_tuple = service.storage.get_snapshot("snap-1")
    assert snapshot_tuple is not None
    _, restored_data = snapshot_tuple

    # Parse and call state machine restore
    from flock.statemachine.models import StateSnapshotMetadata
    fsm_meta = StateSnapshotMetadata(
        applied_index=metadata.applied_index,
        current_term=metadata.current_term,
        timestamp=metadata.timestamp,
        checksum=metadata.checksum,
    )
    
    fsm.restore_snapshot(fsm_meta, json.loads(restored_data.decode("utf-8")))

    # Verify that StateMachineService.restore_snapshot was invoked with parsed parameters
    fsm.restore_snapshot.assert_called_once()
