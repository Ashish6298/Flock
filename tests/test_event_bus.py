"""Tests verifying event publish-subscribe dispatcher workflows."""

import pytest
import asyncio
from typing import Any
from flock.events.bus import EventBus

@pytest.mark.asyncio
async def test_event_bus_pub_sub() -> None:
    bus = EventBus()
    received_data = []

    async def event_handler(data: Any) -> None:
        received_data.append(data)

    bus.subscribe("node.join", event_handler)
    await bus.publish("node.join", {"node_id": "test-node"})

    assert len(received_data) == 1
    assert received_data[0]["node_id"] == "test-node"

    # Unsubscribe verify
    bus.unsubscribe("node.join", event_handler)
    await bus.publish("node.join", {"node_id": "test-node"})
    assert len(received_data) == 1
