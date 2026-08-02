"""Unit and integration tests for the Plugin Event Bus."""

from __future__ import annotations

import pytest
from typing import List

from flock.plugins.models import PluginEvent, PluginEventPriority
from flock.plugins.registry import PluginRegistry
from flock.plugins.events import PluginEventBus


def test_event_bus_pub_sub_happy_path() -> None:
    registry = PluginRegistry()
    bus = PluginEventBus(registry)
    received_events: List[PluginEvent] = []

    def on_event(event: PluginEvent) -> None:
        received_events.append(event)

    sub_id = bus.subscribe(
        plugin_id="plugin-a",
        event_type="metrics.cpu",
        callback=on_event,
    )
    assert sub_id is not None

    event = PluginEvent(
        event_id="evt-1",
        event_type="metrics.cpu",
        sender_id="system",
        payload={"usage": 45.2},
    )
    invoked = bus.publish(event)
    assert invoked == 1
    assert len(received_events) == 1
    assert received_events[0].event_id == "evt-1"
    assert received_events[0].payload["usage"] == 45.2


def test_event_bus_priority_ordering() -> None:
    registry = PluginRegistry()
    bus = PluginEventBus(registry)
    received_ids: List[str] = []

    # Subscribe with normal priority filter
    bus.subscribe(
        plugin_id="plugin-b",
        event_type="alert",
        callback=lambda e: received_ids.append("b"),
        priority_filter=PluginEventPriority.HIGH,
    )
    # Subscribe with critical priority filter
    bus.subscribe(
        plugin_id="plugin-c",
        event_type="alert",
        callback=lambda e: received_ids.append("c"),
        priority_filter=PluginEventPriority.CRITICAL,
    )

    # Publish high event: only B should receive it
    event_high = PluginEvent(
        event_id="evt-high",
        event_type="alert",
        sender_id="plugin-a",
        priority=PluginEventPriority.HIGH,
    )
    invoked = bus.publish(event_high)
    assert invoked == 1
    assert received_ids == ["b"]


def test_event_bus_unsubscribe() -> None:
    registry = PluginRegistry()
    bus = PluginEventBus(registry)
    received_events: List[PluginEvent] = []

    sub_id = bus.subscribe(
        plugin_id="plugin-a",
        event_type="metrics.cpu",
        callback=lambda e: received_events.append(e),
    )
    
    # Unsubscribe
    unsubscribed = bus.unsubscribe(sub_id)
    assert unsubscribed is True

    event = PluginEvent(
        event_id="evt-1",
        event_type="metrics.cpu",
        sender_id="system",
    )
    invoked = bus.publish(event)
    assert invoked == 0
    assert len(received_events) == 0


def test_event_bus_fault_isolation() -> None:
    registry = PluginRegistry()
    bus = PluginEventBus(registry)
    invoked_good = False

    def bad_callback(event: PluginEvent) -> None:
        raise RuntimeError("Bad subscriber failed")

    def good_callback(event: PluginEvent) -> None:
        nonlocal invoked_good
        invoked_good = True

    bus.subscribe("plugin-bad", "test.event", bad_callback)
    bus.subscribe("plugin-good", "test.event", good_callback)

    event = PluginEvent(
        event_id="evt-fail",
        event_type="test.event",
        sender_id="system",
    )
    invoked = bus.publish(event)
    # The dispatcher continues to the next subscriber after failure
    assert invoked == 1
    assert invoked_good is True
