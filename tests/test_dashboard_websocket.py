"""Unit tests for WebSocketBroadcaster."""

import pytest

from flock.dashboard.websocket import WebSocketBroadcaster
from flock.dashboard.models import WebSocketMessage
from flock.dashboard.exceptions import WebSocketError


def test_subscribe_and_broadcast() -> None:
    received: list[str] = []
    bc = WebSocketBroadcaster()
    bc.subscribe("metrics", lambda m: received.append(m.channel))
    msg = WebSocketMessage(channel="metrics", payload={"value": 1})
    delivered = bc.broadcast(msg)
    assert delivered == 1
    assert received == ["metrics"]


def test_broadcast_to_unsubscribed_channel() -> None:
    bc = WebSocketBroadcaster()
    msg = WebSocketMessage(channel="empty", payload={})
    assert bc.broadcast(msg) == 0


def test_unsubscribe() -> None:
    received: list[int] = []
    handler = lambda m: received.append(1)  # noqa: E731
    bc = WebSocketBroadcaster()
    bc.subscribe("ch", handler)
    bc.unsubscribe("ch", handler)
    bc.broadcast(WebSocketMessage(channel="ch", payload={}))
    assert received == []


def test_unsubscribe_missing_channel_raises() -> None:
    bc = WebSocketBroadcaster()
    with pytest.raises(WebSocketError):
        bc.unsubscribe("ghost", lambda m: None)


def test_broadcast_to_all() -> None:
    counts: list[int] = []
    bc = WebSocketBroadcaster()
    bc.subscribe("a", lambda m: counts.append(1))
    bc.subscribe("b", lambda m: counts.append(1))
    total = bc.broadcast_to_all({"x": 1})
    assert total == 2


def test_subscriber_count() -> None:
    bc = WebSocketBroadcaster()
    bc.subscribe("ch", lambda m: None)
    bc.subscribe("ch", lambda m: None)
    assert bc.subscriber_count("ch") == 2


def test_total_subscribers() -> None:
    bc = WebSocketBroadcaster()
    bc.subscribe("a", lambda m: None)
    bc.subscribe("b", lambda m: None)
    assert bc.total_subscribers() == 2


def test_message_count_increments() -> None:
    bc = WebSocketBroadcaster()
    bc.subscribe("ch", lambda m: None)
    bc.broadcast(WebSocketMessage(channel="ch", payload={}))
    bc.broadcast(WebSocketMessage(channel="ch", payload={}))
    assert bc.message_count == 2


def test_faulty_handler_isolated() -> None:
    bc = WebSocketBroadcaster()
    bc.subscribe("ch", lambda m: 1 / 0)  # Will raise ZeroDivisionError
    # Should not propagate
    delivered = bc.broadcast(WebSocketMessage(channel="ch", payload={}))
    assert delivered == 0


def test_clear() -> None:
    bc = WebSocketBroadcaster()
    bc.subscribe("ch", lambda m: None)
    bc.clear()
    assert bc.total_subscribers() == 0
