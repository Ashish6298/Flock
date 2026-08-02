"""Plugin Lifecycle Engine.

Implements deterministic lifecycle state management for plugins, enforcing
legal state transitions, recording complete transition history, and
dispatching lifecycle events through the PluginEventDispatcher.

All operations are thread-safe using RLock. Invalid state transitions raise
PluginInvalidTransitionError immediately without side effects.
"""

from __future__ import annotations

import threading
from typing import Dict, FrozenSet, List, Optional, Tuple

import structlog

from flock.plugins.exceptions import (
    PluginInvalidTransitionError,
    PluginLifecycleStateError,
    PluginNotFoundError,
)
from flock.plugins.lifecycle_models import (
    PluginEventType,
    PluginLifecycleState,
    PluginLifecycleTransition,
    PluginStatus,
)
from flock.plugins.events import PluginEventDispatcher
from flock.plugins.models import PluginManifest

logger = structlog.get_logger()

# ---------------------------------------------------------------------------
# Legal Transition Table
# ---------------------------------------------------------------------------
# Maps (from_state) -> frozenset of allowed (to_state) values.
_LEGAL_TRANSITIONS: Dict[PluginLifecycleState, FrozenSet[PluginLifecycleState]] = {
    PluginLifecycleState.UNREGISTERED: frozenset({PluginLifecycleState.REGISTERED}),
    PluginLifecycleState.REGISTERED: frozenset({
        PluginLifecycleState.LOADED,
        PluginLifecycleState.VALIDATION_FAILED,
        PluginLifecycleState.UNREGISTERED,
    }),
    PluginLifecycleState.VALIDATION_FAILED: frozenset({PluginLifecycleState.UNREGISTERED}),
    PluginLifecycleState.LOADED: frozenset({
        PluginLifecycleState.INITIALIZED,
        PluginLifecycleState.INITIALIZATION_FAILED,
        PluginLifecycleState.UNLOADED,
    }),
    PluginLifecycleState.INITIALIZATION_FAILED: frozenset({PluginLifecycleState.UNLOADED}),
    PluginLifecycleState.INITIALIZED: frozenset({
        PluginLifecycleState.ACTIVE,
        PluginLifecycleState.ACTIVATION_FAILED,
        PluginLifecycleState.UNLOADED,
    }),
    PluginLifecycleState.ACTIVATION_FAILED: frozenset({
        PluginLifecycleState.UNLOADED,
        PluginLifecycleState.INITIALIZED,
    }),
    PluginLifecycleState.ACTIVE: frozenset({
        PluginLifecycleState.SUSPENDED,
        PluginLifecycleState.INACTIVE,
        PluginLifecycleState.UNLOADED,
        PluginLifecycleState.ERROR,
    }),
    PluginLifecycleState.SUSPENDED: frozenset({
        PluginLifecycleState.ACTIVE,
        PluginLifecycleState.UNLOADED,
        PluginLifecycleState.ERROR,
    }),
    PluginLifecycleState.INACTIVE: frozenset({
        PluginLifecycleState.ACTIVE,
        PluginLifecycleState.UNLOADED,
    }),
    PluginLifecycleState.ERROR: frozenset({
        PluginLifecycleState.UNLOADED,
        PluginLifecycleState.INACTIVE,
    }),
    PluginLifecycleState.UNLOADED: frozenset({PluginLifecycleState.CLEANED_UP}),
    PluginLifecycleState.CLEANED_UP: frozenset(),  # terminal state
}

# Maps (from_state, to_state) -> PluginEventType for automated event dispatch.
_TRANSITION_EVENTS: Dict[Tuple[PluginLifecycleState, PluginLifecycleState], PluginEventType] = {
    (PluginLifecycleState.UNREGISTERED, PluginLifecycleState.REGISTERED): PluginEventType.PLUGIN_REGISTERED,
    (PluginLifecycleState.REGISTERED, PluginLifecycleState.UNREGISTERED): PluginEventType.PLUGIN_UNREGISTERED,
    (PluginLifecycleState.REGISTERED, PluginLifecycleState.LOADED): PluginEventType.PLUGIN_LOADED,
    (PluginLifecycleState.LOADED, PluginLifecycleState.INITIALIZED): PluginEventType.PLUGIN_INITIALIZED,
    (PluginLifecycleState.INITIALIZED, PluginLifecycleState.ACTIVE): PluginEventType.PLUGIN_ACTIVATED,
    (PluginLifecycleState.ACTIVE, PluginLifecycleState.INACTIVE): PluginEventType.PLUGIN_DEACTIVATED,
    (PluginLifecycleState.INACTIVE, PluginLifecycleState.ACTIVE): PluginEventType.PLUGIN_ACTIVATED,
    (PluginLifecycleState.ACTIVE, PluginLifecycleState.SUSPENDED): PluginEventType.PLUGIN_SUSPENDED,
    (PluginLifecycleState.SUSPENDED, PluginLifecycleState.ACTIVE): PluginEventType.PLUGIN_RESUMED,
    (PluginLifecycleState.ACTIVE, PluginLifecycleState.UNLOADED): PluginEventType.PLUGIN_UNLOADED,
    (PluginLifecycleState.UNLOADED, PluginLifecycleState.CLEANED_UP): PluginEventType.PLUGIN_CLEANED_UP,
}


class PluginLifecycleEngine:
    """Deterministic plugin lifecycle state machine with full transition history.

    Maintains per-plugin lifecycle state, validates transitions against the
    legal transition table, records every transition to an immutable history,
    and dispatches lifecycle events through a ``PluginEventDispatcher``.

    Thread Safety:
        All state reads and writes are protected by a reentrant lock (RLock).
        Transition validation and state update occur atomically within the
        same lock scope, preventing race conditions under concurrent access.
    """

    def __init__(self, dispatcher: Optional[PluginEventDispatcher] = None) -> None:
        self._lock: threading.RLock = threading.RLock()
        self._dispatcher: PluginEventDispatcher = dispatcher or PluginEventDispatcher()
        # plugin_id -> current state
        self._states: Dict[str, PluginLifecycleState] = {}
        # plugin_id -> ordered list of transitions
        self._history: Dict[str, List[PluginLifecycleTransition]] = {}
        # plugin_id -> PluginStatus metadata
        self._statuses: Dict[str, PluginStatus] = {}

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------

    def register(self, manifest: PluginManifest) -> None:
        """Register a plugin, setting its initial state to REGISTERED.

        Args:
            manifest: The validated plugin manifest.

        Raises:
            PluginLifecycleStateError: If the plugin is already tracked.
        """
        with self._lock:
            if manifest.plugin_id in self._states:
                raise PluginLifecycleStateError(
                    f"Plugin '{manifest.plugin_id}' is already tracked by the lifecycle engine."
                )
            self._states[manifest.plugin_id] = PluginLifecycleState.REGISTERED
            self._history[manifest.plugin_id] = []
            self._statuses[manifest.plugin_id] = PluginStatus(
                plugin_id=manifest.plugin_id,
                name=manifest.name,
                version=manifest.version,
                state=PluginLifecycleState.REGISTERED,
                last_transition_at=None,
                error_message=None,
            )
            self._record_transition(
                manifest.plugin_id,
                PluginLifecycleState.UNREGISTERED,
                PluginLifecycleState.REGISTERED,
                PluginEventType.PLUGIN_REGISTERED,
            )

        # Dispatch outside lock to avoid deadlock if listeners re-enter
        self._dispatcher.dispatch_state_change(
            plugin_id=manifest.plugin_id,
            new_state=PluginLifecycleState.REGISTERED,
            event_type=PluginEventType.PLUGIN_REGISTERED,
        )

        logger.info("Plugin registered in lifecycle engine", plugin_id=manifest.plugin_id)


    def unregister(self, plugin_id: str) -> None:
        """Remove a plugin from lifecycle tracking entirely.

        Args:
            plugin_id: The plugin to remove.

        Raises:
            PluginNotFoundError: If the plugin is not tracked.
        """
        with self._lock:
            if plugin_id not in self._states:
                raise PluginNotFoundError(f"Plugin '{plugin_id}' is not tracked by the lifecycle engine.")
            self._states.pop(plugin_id)
            self._history.pop(plugin_id, None)
            self._statuses.pop(plugin_id, None)

        logger.info("Plugin unregistered from lifecycle engine", plugin_id=plugin_id)

    # ------------------------------------------------------------------
    # Transition API
    # ------------------------------------------------------------------

    def transition(
        self,
        plugin_id: str,
        to_state: PluginLifecycleState,
        message: Optional[str] = None,
        error: Optional[str] = None,
    ) -> PluginLifecycleTransition:
        """Perform a validated state transition for a plugin.

        Args:
            plugin_id: The plugin whose state should change.
            to_state: The desired target state.
            message: Optional human-readable description of the transition.
            error: Optional error message for failure transitions.

        Returns:
            The immutable ``PluginLifecycleTransition`` record.

        Raises:
            PluginNotFoundError: If the plugin is not tracked.
            PluginInvalidTransitionError: If the transition is not legal.
        """
        with self._lock:
            if plugin_id not in self._states:
                raise PluginNotFoundError(f"Plugin '{plugin_id}' is not tracked by the lifecycle engine.")

            from_state = self._states[plugin_id]

            # Validate the transition
            allowed = _LEGAL_TRANSITIONS.get(from_state, frozenset())
            if to_state not in allowed:
                raise PluginInvalidTransitionError(plugin_id, from_state.value, to_state.value)

            # Determine event type
            event_type = _TRANSITION_EVENTS.get(
                (from_state, to_state), PluginEventType.PLUGIN_STATE_CHANGED
            )

            # Apply transition
            self._states[plugin_id] = to_state
            record = self._record_transition(
                plugin_id, from_state, to_state, event_type, message=message, error=error
            )

        # Dispatch event outside lock to avoid deadlock if listeners re-enter
        self._dispatcher.dispatch_state_change(
            plugin_id=plugin_id,
            new_state=to_state,
            event_type=event_type,
            error=error,
        )

        logger.info(
            "Plugin lifecycle transition",
            plugin_id=plugin_id,
            from_state=from_state.value,
            to_state=to_state.value,
            event_type=event_type.value,
        )
        return record

    # ------------------------------------------------------------------
    # Convenience Transition Helpers
    # ------------------------------------------------------------------

    def mark_loaded(self, plugin_id: str) -> PluginLifecycleTransition:
        """Transition plugin from REGISTERED → LOADED."""
        return self.transition(plugin_id, PluginLifecycleState.LOADED)

    def mark_initialized(self, plugin_id: str) -> PluginLifecycleTransition:
        """Transition plugin from LOADED → INITIALIZED."""
        return self.transition(plugin_id, PluginLifecycleState.INITIALIZED)

    def mark_active(self, plugin_id: str) -> PluginLifecycleTransition:
        """Transition plugin from INITIALIZED or INACTIVE → ACTIVE."""
        return self.transition(plugin_id, PluginLifecycleState.ACTIVE)

    def mark_inactive(self, plugin_id: str) -> PluginLifecycleTransition:
        """Transition plugin from ACTIVE → INACTIVE."""
        return self.transition(plugin_id, PluginLifecycleState.INACTIVE)

    def mark_suspended(self, plugin_id: str) -> PluginLifecycleTransition:
        """Transition plugin from ACTIVE → SUSPENDED."""
        return self.transition(plugin_id, PluginLifecycleState.SUSPENDED)

    def mark_resumed(self, plugin_id: str) -> PluginLifecycleTransition:
        """Transition plugin from SUSPENDED → ACTIVE."""
        return self.transition(plugin_id, PluginLifecycleState.ACTIVE, message="resumed")

    def mark_unloaded(self, plugin_id: str) -> PluginLifecycleTransition:
        """Transition plugin to UNLOADED from any valid predecessor state."""
        return self.transition(plugin_id, PluginLifecycleState.UNLOADED)

    def mark_cleaned_up(self, plugin_id: str) -> PluginLifecycleTransition:
        """Transition plugin from UNLOADED → CLEANED_UP."""
        return self.transition(plugin_id, PluginLifecycleState.CLEANED_UP)

    def mark_failed(
        self, plugin_id: str, target: PluginLifecycleState, error: str
    ) -> PluginLifecycleTransition:
        """Transition plugin to a failure state with an error message.

        Args:
            plugin_id: The plugin that failed.
            target: One of VALIDATION_FAILED, INITIALIZATION_FAILED, ACTIVATION_FAILED, ERROR.
            error: Description of the failure.
        """
        return self.transition(plugin_id, target, error=error)

    # ------------------------------------------------------------------
    # Query API
    # ------------------------------------------------------------------

    def get_state(self, plugin_id: str) -> PluginLifecycleState:
        """Return the current lifecycle state of a plugin.

        Raises:
            PluginNotFoundError: If plugin is not tracked.
        """
        with self._lock:
            if plugin_id not in self._states:
                raise PluginNotFoundError(f"Plugin '{plugin_id}' is not tracked.")
            return self._states[plugin_id]

    def get_history(self, plugin_id: str) -> List[PluginLifecycleTransition]:
        """Return the complete ordered transition history for a plugin.

        Raises:
            PluginNotFoundError: If plugin is not tracked.
        """
        with self._lock:
            if plugin_id not in self._history:
                raise PluginNotFoundError(f"Plugin '{plugin_id}' is not tracked.")
            return list(self._history[plugin_id])

    def get_status(self, plugin_id: str) -> PluginStatus:
        """Return the current PluginStatus snapshot.

        Raises:
            PluginNotFoundError: If plugin is not tracked.
        """
        with self._lock:
            if plugin_id not in self._statuses:
                raise PluginNotFoundError(f"Plugin '{plugin_id}' is not tracked.")
            return self._statuses[plugin_id]

    def list_all_states(self) -> Dict[str, PluginLifecycleState]:
        """Return a snapshot of all tracked plugins and their current states."""
        with self._lock:
            return dict(self._states)

    def is_active(self, plugin_id: str) -> bool:
        """Return True if plugin is currently in ACTIVE state."""
        with self._lock:
            return self._states.get(plugin_id) == PluginLifecycleState.ACTIVE

    @property
    def dispatcher(self) -> PluginEventDispatcher:
        """Return the bound event dispatcher."""
        return self._dispatcher

    # ------------------------------------------------------------------
    # Internal Helpers
    # ------------------------------------------------------------------

    def _record_transition(
        self,
        plugin_id: str,
        from_state: PluginLifecycleState,
        to_state: PluginLifecycleState,
        event_type: PluginEventType,
        message: Optional[str] = None,
        error: Optional[str] = None,
    ) -> PluginLifecycleTransition:
        """Record a transition and update the PluginStatus snapshot.

        Must be called while holding self._lock.
        """
        record = PluginLifecycleTransition(
            plugin_id=plugin_id,
            from_state=from_state,
            to_state=to_state,
            event_type=event_type,
            message=message,
            error=error,
        )
        self._history[plugin_id].append(record)

        # Rebuild PluginStatus
        old_status = self._statuses.get(plugin_id)
        if old_status is not None:
            self._statuses[plugin_id] = PluginStatus(
                plugin_id=old_status.plugin_id,
                name=old_status.name,
                version=old_status.version,
                state=to_state,
                enabled=old_status.enabled,
                registered_at=old_status.registered_at,
                last_transition_at=record.timestamp,
                transition_count=old_status.transition_count + 1,
                error_message=error,
            )
        return record
