"""Unit tests verifying PeerRegistry catalog behavior."""

import pytest
import time
from flock.discovery.models import NodeDescription
from flock.discovery.registry import PeerRegistry

def test_registry_registration_and_updates() -> None:
    registry = PeerRegistry(expiration_seconds=10.0)
    desc = NodeDescription(node_id="node-1", host="127.0.0.1", port=9001)

    # Initial register
    is_new = registry.register(desc)
    assert is_new is True
    assert len(registry.list_peers()) == 1

    # Update metadata
    desc_updated = NodeDescription(node_id="node-1", host="127.0.0.1", port=9001, capabilities=["scheduler"])
    is_new_update = registry.register(desc_updated)
    assert is_new_update is False
    assert registry.get_peer("node-1").capabilities == ["scheduler"] # type: ignore

def test_registry_expiration() -> None:
    # Set immediate expiration to verify cleanup
    registry = PeerRegistry(expiration_seconds=0.1)
    desc = NodeDescription(node_id="node-2", host="127.0.0.1", port=9002)

    registry.register(desc)
    assert len(registry.list_peers()) == 1

    time.sleep(0.15)
    assert len(registry.list_peers()) == 0

def test_registry_unregister() -> None:
    registry = PeerRegistry(expiration_seconds=10.0)
    desc = NodeDescription(node_id="node-3", host="127.0.0.1", port=9003)

    registry.register(desc)
    assert registry.unregister("node-3") is True
    assert registry.unregister("node-3") is False
