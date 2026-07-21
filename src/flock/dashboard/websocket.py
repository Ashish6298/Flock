"""Dashboard WebSocket Broadcaster.

Manages a registry of in-process WebSocket channel subscribers and
dispatches :class:`~flock.dashboard.models.WebSocketMessage` payloads
to them.  The design is transport-independent: the actual WebSocket
connection management is delegated to the HTTP server layer; this
class handles only channel routing and fan-out logic.
"""

from __future__ import annotations

import threading
from typing import Callable, Dict, List, Set

from flock.dashboard.exceptions import WebSocketError
from flock.dashboard.models import WebSocketMessage


# Type alias for subscriber callables.
MessageHandler = Callable[[WebSocketMessage], None]


class WebSocketBroadcaster:
    """Thread-safe in-process WebSocket channel broadcaster.

    Subscribers register against named channels.  When a message is
    broadcast on a channel all registered handlers receive it.  A
    handler exception is isolated so it cannot crash the broadcast loop.

    Attributes:
        _lock: Reentrant lock protecting the subscription table.
        _channels: Mapping of channel name to set of handler callables.
        _message_count: Total messages broadcast since instantiation.
    """

    def __init__(self) -> None:
        """Initialise an empty broadcaster."""
        self._lock: threading.RLock = threading.RLock()
        self._channels: Dict[str, List[MessageHandler]] = {}
        self._message_count: int = 0

    # ------------------------------------------------------------------
    # Subscription
    # ------------------------------------------------------------------

    def subscribe(self, channel: str, handler: MessageHandler) -> None:
        """Subscribe a handler to a named channel.

        Args:
            channel: Channel name to subscribe to.
            handler: Callable that receives :class:`WebSocketMessage`
                instances published to the channel.
        """
        with self._lock:
            if channel not in self._channels:
                self._channels[channel] = []
            self._channels[channel].append(handler)

    def unsubscribe(self, channel: str, handler: MessageHandler) -> None:
        """Unsubscribe a handler from a channel.

        Args:
            channel: Channel name to unsubscribe from.
            handler: The handler callable to remove.

        Raises:
            WebSocketError: If the channel does not exist or the handler
                is not subscribed.
        """
        with self._lock:
            if channel not in self._channels:
                raise WebSocketError(
                    f"Channel '{channel}' has no subscribers."
                )
            try:
                self._channels[channel].remove(handler)
            except ValueError as exc:
                raise WebSocketError(
                    f"Handler is not subscribed to channel '{channel}'."
                ) from exc
            if not self._channels[channel]:
                del self._channels[channel]

    def unsubscribe_all(self, channel: str) -> None:
        """Remove all subscribers from a channel.

        Args:
            channel: Channel name to clear.
        """
        with self._lock:
            self._channels.pop(channel, None)

    # ------------------------------------------------------------------
    # Broadcasting
    # ------------------------------------------------------------------

    def broadcast(self, message: WebSocketMessage) -> int:
        """Deliver a message to all subscribers of its channel.

        Args:
            message: The :class:`WebSocketMessage` to broadcast.

        Returns:
            The number of handlers that received the message.
        """
        with self._lock:
            handlers = list(self._channels.get(message.channel, []))

        delivered = 0
        for handler in handlers:
            try:
                handler(message)
                delivered += 1
            except Exception:
                pass  # Isolate faulty handlers.

        with self._lock:
            self._message_count += 1

        return delivered

    def broadcast_to_all(self, payload: dict) -> int:  # type: ignore[type-arg]
        """Broadcast a payload to every registered channel.

        A separate :class:`WebSocketMessage` is created for each
        channel, ensuring per-channel routing semantics are preserved.

        Args:
            payload: Payload dict to broadcast everywhere.

        Returns:
            Total number of handler invocations delivered.
        """
        with self._lock:
            channels = list(self._channels.keys())

        total = 0
        for channel in channels:
            msg = WebSocketMessage(channel=channel, payload=payload)
            total += self.broadcast(msg)
        return total

    # ------------------------------------------------------------------
    # Introspection
    # ------------------------------------------------------------------

    def list_channels(self) -> List[str]:
        """Return the names of all active channels."""
        with self._lock:
            return list(self._channels.keys())

    def subscriber_count(self, channel: str) -> int:
        """Return the number of subscribers for a channel."""
        with self._lock:
            return len(self._channels.get(channel, []))

    def total_subscribers(self) -> int:
        """Return the total number of subscriptions across all channels."""
        with self._lock:
            return sum(len(h) for h in self._channels.values())

    def channel_exists(self, channel: str) -> bool:
        """Return ``True`` if the channel has at least one subscriber."""
        with self._lock:
            return channel in self._channels

    @property
    def message_count(self) -> int:
        """Total number of messages broadcast since instantiation."""
        with self._lock:
            return self._message_count

    def active_channels(self) -> Set[str]:
        """Return a snapshot set of all active channel names."""
        with self._lock:
            return set(self._channels.keys())

    def clear(self) -> None:
        """Remove all channel subscriptions."""
        with self._lock:
            self._channels.clear()
