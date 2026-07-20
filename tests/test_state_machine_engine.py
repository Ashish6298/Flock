"""Unit tests for StateMachineEngine."""

import asyncio
import json
import time
from typing import Dict, Any
import pytest
from flock.events.bus import EventBus
from flock.statemachine.exceptions import StateMachineError
from flock.statemachine.engine import StateMachineEngine
from flock.statemachine.models import StateCommand, StateOperation
from flock.statemachine.store import ReplicatedStateStore


def test_engine_idempotency_duplicate_commands() -> None:
    events = EventBus()
    store = ReplicatedStateStore()
    engine = StateMachineEngine(store, events)

    cmd = StateCommand(
        command_id="cmd-123",
        operation=StateOperation.PUT,
        key="x",
        value=100,
        timestamp=time.time(),
    )
    cmd_bytes = json.dumps(cmd.model_dump()).encode("utf-8")

    # Apply first time
    entry1 = engine.apply_entry(index=1, term=1, command_data=cmd_bytes)
    assert entry1 is not None
    assert entry1.value == 100
    assert engine.applied_index == 1

    # Apply duplicate Command ID (with next index)
    entry2 = engine.apply_entry(index=2, term=1, command_data=cmd_bytes)
    assert entry2 is None  # Skipped as duplicate
    assert engine.applied_index == 2  # Index advanced to preserve consensus pipeline


def test_engine_out_of_order_reject() -> None:
    events = EventBus()
    store = ReplicatedStateStore()
    engine = StateMachineEngine(store, events)

    cmd = StateCommand(
        command_id="c1",
        operation=StateOperation.PUT,
        key="x",
        value=10,
        timestamp=time.time(),
    )
    cmd_bytes = json.dumps(cmd.model_dump()).encode("utf-8")

    # Initial applied index is 0, trying to apply index 2 directly should raise StateMachineError
    with pytest.raises(StateMachineError):
        engine.apply_entry(index=2, term=1, command_data=cmd_bytes)


@pytest.mark.asyncio
async def test_engine_event_bus_publishing() -> None:
    events = EventBus()
    store = ReplicatedStateStore()
    engine = StateMachineEngine(store, events)

    received_events = []
    applied_events = []

    async def on_received(data: Dict[str, Any]) -> None:
        received_events.append(data)

    async def on_applied(data: Dict[str, Any]) -> None:
        applied_events.append(data)

    events.subscribe("state.command.received", on_received)
    events.subscribe("state.command.applied", on_applied)

    cmd = StateCommand(
        command_id="c1",
        operation=StateOperation.PUT,
        key="x",
        value=50,
        timestamp=time.time(),
    )
    cmd_bytes = json.dumps(cmd.model_dump()).encode("utf-8")
    engine.apply_entry(index=1, term=1, command_data=cmd_bytes)

    # Let the event loop run tasks
    await asyncio.sleep(0.01)

    assert len(received_events) == 1
    assert received_events[0]["command_id"] == "c1"
    assert len(applied_events) == 1
    assert applied_events[0]["command_id"] == "c1"
