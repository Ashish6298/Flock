"""Plugin Event Dispatcher.

Implements a synchronous event dispatcher that allows listeners to subscribe
to plugin lifecycle events. The dispatcher guarantees that one failing listener
cannot interrupt event delivery to remaining listeners. All operations are
thread-safe using RLock.
"""

from __future__ import annotations

import threading
import uuid
from typing import Callable, Dict, List, Optional, Any
import structlog
from flock.plugins.models import PluginEvent, PluginSubscription, PluginEventPriority
from flock.plugins.registry import PluginRegistry

from flock.plugins.lifecycle_models import (
    PluginEventPayload,
    PluginEventSubscription,
    PluginEventType,
    PluginLifecycleState,
)

logger = structlog.get_logger()

# A listener callable receives a PluginEventPayload and returns nothing.
EventListener = Callable[[PluginEventPayload], None]


class PluginEventDispatcher:
    """Thread-safe synchronous event dispatcher for plugin lifecycle events.

    Listeners are registered per event type. When an event is dispatched, all
    registered listeners for that event type are invoked in registration order.
    Exceptions raised by individual listeners are caught, logged, and never
    allowed to interrupt delivery to subsequent listeners.
    """

    def __init__(self) -> None:
        self._lock: threading.RLock = threading.RLock()
        # event_type -> list of (subscription_id, listener)
        self._listeners: Dict[PluginEventType, List[tuple[str, EventListener]]] = {}
        self._subscriptions: Dict[str, PluginEventSubscription] = {}

    # ------------------------------------------------------------------
    # Subscription Management
    # ------------------------------------------------------------------

    def subscribe(
        self,
        event_type: PluginEventType,
        listener: EventListener,
        listener_name: str,
        plugin_id: Optional[str] = None,
    ) -> str:
        """Subscribe a listener to a plugin lifecycle event type.

        Args:
            event_type: The event type to subscribe to.
            listener: Callable accepting a ``PluginEventPayload``.
            listener_name: Human-readable name for diagnostics.
            plugin_id: If provided, only events from this plugin are delivered.

        Returns:
            A unique subscription ID string for later unsubscription.
        """
        subscription_id = str(uuid.uuid4())
        record = PluginEventSubscription(
            subscription_id=subscription_id,
            event_type=event_type,
            listener_name=listener_name,
            plugin_id=plugin_id,
        )
        with self._lock:
            if event_type not in self._listeners:
                self._listeners[event_type] = []
            self._listeners[event_type].append((subscription_id, listener))
            self._subscriptions[subscription_id] = record

        logger.debug(
            "Plugin event listener subscribed",
            subscription_id=subscription_id,
            event_type=event_type.value,
            listener_name=listener_name,
        )
        return subscription_id

    def unsubscribe(self, subscription_id: str) -> bool:
        """Remove a subscription by its ID.

        Args:
            subscription_id: The ID returned by ``subscribe``.

        Returns:
            True if the subscription was found and removed, False otherwise.
        """
        with self._lock:
            record = self._subscriptions.pop(subscription_id, None)
            if record is None:
                return False
            listeners = self._listeners.get(record.event_type, [])
            self._listeners[record.event_type] = [
                (sid, fn) for sid, fn in listeners if sid != subscription_id
            ]
        return True

    def list_subscriptions(self) -> List[PluginEventSubscription]:
        """Return all active subscription records."""
        with self._lock:
            return list(self._subscriptions.values())

    # ------------------------------------------------------------------
    # Event Dispatch
    # ------------------------------------------------------------------

    def dispatch(self, payload: PluginEventPayload) -> int:
        """Dispatch an event payload to all matching listeners.

        Listeners subscribed to a specific ``plugin_id`` only receive events
        whose payload ``plugin_id`` matches. Listeners with no ``plugin_id``
        filter receive all events of the subscribed type.

        Exceptions raised by individual listeners are caught, logged, and
        execution continues to remaining listeners.

        Args:
            payload: The structured event payload to dispatch.

        Returns:
            The number of listeners successfully invoked.
        """
        with self._lock:
            listeners_snapshot = list(self._listeners.get(payload.event_type, []))
            subs_snapshot = dict(self._subscriptions)

        invoked = 0
        for subscription_id, listener in listeners_snapshot:
            sub = subs_snapshot.get(subscription_id)
            if sub is None:
                continue
            # Apply per-plugin filter if set
            if sub.plugin_id is not None and sub.plugin_id != payload.plugin_id:
                continue
            try:
                listener(payload)
                invoked += 1
            except Exception as exc:
                logger.error(
                    "Plugin event listener raised an exception; continuing dispatch",
                    subscription_id=subscription_id,
                    listener_name=sub.listener_name,
                    event_type=payload.event_type.value,
                    plugin_id=payload.plugin_id,
                    error=str(exc),
                )
        return invoked

    def dispatch_state_change(
        self,
        plugin_id: str,
        new_state: PluginLifecycleState,
        event_type: PluginEventType,
        error: Optional[str] = None,
    ) -> int:
        """Convenience helper to build and dispatch a state-change payload.

        Args:
            plugin_id: The plugin whose state changed.
            new_state: The state the plugin transitioned into.
            event_type: The event type associated with this transition.
            error: Optional error message for failure events.

        Returns:
            The number of listeners successfully invoked.
        """
        payload = PluginEventPayload(
            plugin_id=plugin_id,
            event_type=event_type,
            state=new_state,
            error=error,
        )
        return self.dispatch(payload)





class PluginEventBus:
    """Thread-safe in-process event bus for loosely coupled plugin communication.

    Supports publishing, subscribing, broadcasting, priority-ordered dispatch,
    filtering by event type, and fault-isolated dispatch to multiple subscribers.
    """

    def __init__(self, registry: PluginRegistry) -> None:
        self._registry = registry
        self._lock = threading.RLock()
        self._subscribers: Dict[str, Callable[[PluginEvent], None]] = {}  # sub_id -> callback

    def subscribe(
        self,
        plugin_id: str,
        event_type: str,
        callback: Callable[[PluginEvent], None],
        priority_filter: Optional[PluginEventPriority] = None,
    ) -> str:
        """Subscribes a plugin callback to an event type."""
        sub_id = str(uuid.uuid4())
        sub = PluginSubscription(
            subscription_id=sub_id,
            plugin_id=plugin_id,
            event_type=event_type,
            priority_filter=priority_filter,
        )
        with self._lock:
            self._registry.register_subscription(sub)
            self._subscribers[sub_id] = callback
        return sub_id

    def unsubscribe(self, subscription_id: str) -> bool:
        """Removes a subscription by its ID."""
        with self._lock:
            self._subscribers.pop(subscription_id, None)
            return self._registry.remove_subscription(subscription_id)

    def publish(self, event: PluginEvent) -> int:
        """Publishes an event to all matching subscribers, ordered by priority."""
        with self._lock:
            # Query matching subscriptions
            subs = self._registry.query_subscriptions(event_type=event.event_type)
            
            # Filter and group subscribers that are active/registered in registry
            # Get callbacks
            callbacks_to_invoke: List[tuple[PluginSubscription, Callable[[PluginEvent], None]]] = []
            for sub in subs:
                callback = self._subscribers.get(sub.subscription_id)
                if callback is not None:
                    # Apply priority filter check if configured
                    if sub.priority_filter is not None and event.priority < sub.priority_filter:
                        continue
                    callbacks_to_invoke.append((sub, callback))

            # Deterministic dispatch order based on priority (highest first)
            # If priorities are equal, sort by subscription_id to guarantee deterministic ordering
            callbacks_to_invoke.sort(
                key=lambda item: (-int(item[0].priority_filter or PluginEventPriority.NORMAL), item[0].subscription_id)
            )

        invoked = 0
        for sub, cb in callbacks_to_invoke:
            try:
                cb(event)
                invoked += 1
            except Exception as exc:
                logger.error(
                    "PluginEventBus subscriber raised exception",
                    subscription_id=sub.subscription_id,
                    plugin_id=sub.plugin_id,
                    event_id=event.event_id,
                    error=str(exc),
                )
        return invoked

    def broadcast(self, sender_id: str, event_type: str, payload: Dict[str, Any], priority: PluginEventPriority = PluginEventPriority.NORMAL) -> int:
        """Convenience method to construct and publish a broadcast event."""
        event = PluginEvent(
            event_id=str(uuid.uuid4()),
            event_type=event_type,
            sender_id=sender_id,
            payload=payload,
            priority=priority,
        )
        return self.publish(event)

