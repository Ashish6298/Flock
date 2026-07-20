"""Unit tests for SnapshotService."""

import asyncio
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
from flock.statemachine.models import StateSnapshotMetadata


@pytest.mark.asyncio
async def test_snapshot_service_creation_pipeline() -> None:
    consensus = MagicMock(spec=ConsensusService)
    consensus._log = MagicMock()
    consensus._log.commit_index = 5
    consensus._log._entries = []

    fsm = MagicMock(spec=StateMachineService)
    # FSM snapshot returns StateSnapshotMetadata & raw dictionary
    # Calculate correct checksum of serialized data
    raw_data = {"state": {"score": 99}}
    data_bytes = json.dumps(raw_data).encode("utf-8")
    import hashlib
    real_checksum = hashlib.sha256(data_bytes).hexdigest()

    fsm_meta = StateSnapshotMetadata(
        applied_index=5,
        current_term=1,
        timestamp=time.time(),
        checksum=real_checksum,
    )
    fsm.snapshot.return_value = (fsm_meta, raw_data)

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

    metadata = await service.create_snapshot()

    assert metadata.applied_index == 5
    assert metadata.snapshot_id == fsm_meta.checksum[:16]
    # Check stored in SnapshotStorage
    assert len(service.storage.list_snapshots()) == 1
