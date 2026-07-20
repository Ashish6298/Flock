"""Unit tests for snapshot generation and restoration."""

import json
import time
from flock.events.bus import EventBus
from flock.statemachine.exceptions import StateMachineError
from flock.statemachine.engine import StateMachineEngine
from flock.statemachine.models import StateCommand, StateOperation
from flock.statemachine.store import ReplicatedStateStore


def test_snapshot_create_and_restore() -> None:
    events = EventBus()
    store = ReplicatedStateStore()
    engine = StateMachineEngine(store, events)

    # 1. Populate store with values
    cmd1 = StateCommand(
        command_id="c1",
        operation=StateOperation.PUT,
        key="username",
        value="alice",
        timestamp=time.time(),
    )
    cmd2 = StateCommand(
        command_id="c2",
        operation=StateOperation.PUT,
        key="balance",
        value=500,
        timestamp=time.time(),
    )

    engine.apply_entry(1, 1, json.dumps(cmd1.model_dump()).encode("utf-8"))
    engine.apply_entry(2, 1, json.dumps(cmd2.model_dump()).encode("utf-8"))

    # Verify initial state
    assert store.get("username").value == "alice"
    assert store.get("balance").value == 500
    assert engine.applied_index == 2

    # 2. Create Snapshot
    metadata, snapshot_data = engine.create_snapshot()
    assert metadata.applied_index == 2
    assert metadata.current_term == 1
    assert "username" in snapshot_data["state"]

    # 3. Create a clean/empty store/engine and restore the snapshot
    store2 = ReplicatedStateStore()
    engine2 = StateMachineEngine(store2, events)
    engine2.restore_snapshot(metadata, snapshot_data)

    # 4. Verify state after restoration
    assert store2.get("username").value == "alice"
    assert store2.get("balance").value == 500
    assert engine2.applied_index == 2
    assert engine2.current_term == 1
