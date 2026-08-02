"""Unit and integration tests for the Plugin Messaging Engine."""

from __future__ import annotations

import pytest
from typing import List

from flock.plugins.models import PluginMessage, PluginBroadcast, PluginManifest
from flock.plugins.registry import PluginRegistry
from flock.plugins.exceptions import (
    PluginMessageValidationError,
    PluginMessageTimeoutError,
    PluginMessageDeliveryError,
)
from flock.plugins.messaging import PluginMessagingEngine


def test_direct_messaging_happy_path() -> None:
    registry = PluginRegistry()
    engine = PluginMessagingEngine(registry)

    # Register fake sender and receiver manifests to satisfy delivery checks
    manifest_sender = PluginManifest(plugin_id="plugin-sender", name="Sender", version="1.0.0", author="test")
    manifest_rec = PluginManifest(plugin_id="plugin-recipient", name="Recipient", version="1.0.0", author="test")
    registry.register_plugin(manifest_sender)
    registry.register_plugin(manifest_rec)

    # Register handler
    def handler(msg: PluginMessage) -> dict:
        return {"reply": f"Hello, {msg.sender_id}"}

    registry.register_message_handler("plugin-recipient", "greet", handler)

    msg = PluginMessage(
        message_id="msg-1",
        sender_id="plugin-sender",
        recipient_id="plugin-recipient",
        subject="greet",
        body={"greeting": "Hi"},
    )

    resp = engine.send_message(msg)
    assert resp.success is True
    assert resp.request_id == "msg-1"
    assert resp.payload["reply"] == "Hello, plugin-sender"


def test_messaging_validation_error() -> None:
    registry = PluginRegistry()
    engine = PluginMessagingEngine(registry)

    # Missing recipient
    msg = PluginMessage(
        message_id="msg-1",
        sender_id="plugin-sender",
        recipient_id="",
        subject="greet",
    )
    with pytest.raises(PluginMessageValidationError):
        engine.send_message(msg)


def test_messaging_delivery_error_missing_recipient() -> None:
    registry = PluginRegistry()
    engine = PluginMessagingEngine(registry)

    # Recipient does not exist in registry
    msg = PluginMessage(
        message_id="msg-1",
        sender_id="plugin-sender",
        recipient_id="missing-recipient",
        subject="greet",
    )
    with pytest.raises(PluginMessageDeliveryError):
        engine.send_message(msg)


def test_messaging_broadcast() -> None:
    registry = PluginRegistry()
    engine = PluginMessagingEngine(registry)

    # Register receiver plugins
    p1 = PluginManifest(plugin_id="p1", name="P1", version="1.0.0", author="test")
    p2 = PluginManifest(plugin_id="p2", name="P2", version="1.0.0", author="test")
    p_sender = PluginManifest(plugin_id="p-sender", name="Sender", version="1.0.0", author="test")
    registry.register_plugin(p1)
    registry.register_plugin(p2)
    registry.register_plugin(p_sender)

    received_subjects: List[str] = []

    def handler(msg: PluginMessage) -> None:
        received_subjects.append(msg.recipient_id)

    registry.register_message_handler("p1", "notify", handler)
    registry.register_message_handler("p2", "notify", handler)

    bcast = PluginBroadcast(
        broadcast_id="bcast-1",
        sender_id="p-sender",
        subject="notify",
        body={"update": "data"},
    )

    delivery_count = engine.send_broadcast(bcast)
    assert delivery_count == 2
    assert "p1" in received_subjects
    assert "p2" in received_subjects
