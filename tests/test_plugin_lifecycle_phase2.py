"""Tests for Milestone E Phase 2 — Plugin Lifecycle & Event System.

Covers:
- PluginLifecycleState enumeration completeness
- PluginEventType enumeration completeness
- PluginLifecycleTransition model construction and immutability
- PluginEventPayload model construction and immutability
- PluginStatus model and field defaults
- PluginEventSubscription model
- PluginEventDispatcher subscribe / unsubscribe / dispatch / filters
- PluginEventDispatcher fault isolation (listener exceptions)
- PluginEventDispatcher dispatch_state_change helper
- PluginLifecycleEngine register / unregister
- PluginLifecycleEngine valid transitions (full happy path)
- PluginLifecycleEngine illegal transition rejection
- PluginLifecycleEngine transition history accuracy
- PluginLifecycleEngine PluginStatus snapshot updates
- PluginLifecycleEngine convenience helpers
- PluginLifecycleEngine query API
- PluginInvalidTransitionError attributes
- Phase 2 exceptions existence and hierarchy
"""

from __future__ import annotations

import time
from typing import List
from unittest.mock import MagicMock

import pytest

from flock.plugins.lifecycle_models import (
    PluginEventPayload,
    PluginEventSubscription,
    PluginEventType,
    PluginLifecycleState,
    PluginLifecycleTransition,
    PluginStatus,
)
from flock.plugins.events import PluginEventDispatcher
from flock.plugins.lifecycle import PluginLifecycleEngine
from flock.plugins.models import PluginManifest
from flock.plugins.exceptions import (
    PluginInvalidTransitionError,
    PluginLifecycleError,
    PluginLifecycleStateError,
    PluginNotFoundError,
    PluginEventDispatchError,
)


# ---------------------------------------------------------------------------
# Helpers / Fixtures
# ---------------------------------------------------------------------------


def _manifest(plugin_id: str = "test-plugin") -> PluginManifest:
    return PluginManifest(
        plugin_id=plugin_id,
        name="Test Plugin",
        version="1.0.0",
        author="tester",
    )


def _engine() -> PluginLifecycleEngine:
    return PluginLifecycleEngine()


# ---------------------------------------------------------------------------
# PluginLifecycleState
# ---------------------------------------------------------------------------


class TestPluginLifecycleState:
    def test_all_states_defined(self) -> None:
        states = {s.value for s in PluginLifecycleState}
        expected = {
            "UNREGISTERED", "REGISTERED", "VALIDATION_FAILED", "LOADED",
            "INITIALIZATION_FAILED", "INITIALIZED", "ACTIVATION_FAILED",
            "ACTIVE", "SUSPENDED", "INACTIVE", "UNLOADED", "CLEANED_UP", "ERROR",
        }
        assert expected.issubset(states)

    def test_state_is_str(self) -> None:
        assert isinstance(PluginLifecycleState.ACTIVE, str)

    def test_state_str_value(self) -> None:
        assert PluginLifecycleState.ACTIVE == "ACTIVE"


# ---------------------------------------------------------------------------
# PluginEventType
# ---------------------------------------------------------------------------


class TestPluginEventType:
    def test_all_event_types_defined(self) -> None:
        types = {e.value for e in PluginEventType}
        expected = {
            "plugin.registered", "plugin.unregistered", "plugin.loaded",
            "plugin.initialized", "plugin.activated", "plugin.deactivated",
            "plugin.suspended", "plugin.resumed", "plugin.unloaded",
            "plugin.cleaned_up", "plugin.failed", "plugin.state_changed",
        }
        assert expected.issubset(types)

    def test_event_type_is_str(self) -> None:
        assert isinstance(PluginEventType.PLUGIN_ACTIVATED, str)


# ---------------------------------------------------------------------------
# PluginLifecycleTransition Model
# ---------------------------------------------------------------------------


class TestPluginLifecycleTransition:
    def test_construction(self) -> None:
        record = PluginLifecycleTransition(
            plugin_id="p1",
            from_state=PluginLifecycleState.REGISTERED,
            to_state=PluginLifecycleState.LOADED,
            event_type=PluginEventType.PLUGIN_LOADED,
        )
        assert record.plugin_id == "p1"
        assert record.from_state == PluginLifecycleState.REGISTERED
        assert record.to_state == PluginLifecycleState.LOADED
        assert record.error is None
        assert isinstance(record.timestamp, float)

    def test_immutable(self) -> None:
        record = PluginLifecycleTransition(
            plugin_id="p1",
            from_state=PluginLifecycleState.REGISTERED,
            to_state=PluginLifecycleState.LOADED,
            event_type=PluginEventType.PLUGIN_LOADED,
        )
        with pytest.raises(Exception):
            record.plugin_id = "other"  # type: ignore[misc]

    def test_with_error(self) -> None:
        record = PluginLifecycleTransition(
            plugin_id="p1",
            from_state=PluginLifecycleState.LOADED,
            to_state=PluginLifecycleState.INITIALIZATION_FAILED,
            event_type=PluginEventType.PLUGIN_FAILED,
            error="init error",
        )
        assert record.error == "init error"


# ---------------------------------------------------------------------------
# PluginEventPayload Model
# ---------------------------------------------------------------------------


class TestPluginEventPayload:
    def test_construction(self) -> None:
        payload = PluginEventPayload(
            plugin_id="p1",
            event_type=PluginEventType.PLUGIN_ACTIVATED,
            state=PluginLifecycleState.ACTIVE,
        )
        assert payload.plugin_id == "p1"
        assert payload.state == PluginLifecycleState.ACTIVE
        assert isinstance(payload.timestamp, float)
        assert payload.error is None

    def test_immutable(self) -> None:
        payload = PluginEventPayload(
            plugin_id="p1",
            event_type=PluginEventType.PLUGIN_ACTIVATED,
            state=PluginLifecycleState.ACTIVE,
        )
        with pytest.raises(Exception):
            payload.plugin_id = "other"  # type: ignore[misc]

    def test_metadata_optional(self) -> None:
        payload = PluginEventPayload(
            plugin_id="p1",
            event_type=PluginEventType.PLUGIN_ACTIVATED,
            state=PluginLifecycleState.ACTIVE,
            metadata={"key": "value"},
        )
        assert payload.metadata["key"] == "value"


# ---------------------------------------------------------------------------
# PluginStatus Model
# ---------------------------------------------------------------------------


class TestPluginStatus:
    def test_construction(self) -> None:
        status = PluginStatus(
            plugin_id="p1",
            name="My Plugin",
            version="2.0.0",
            state=PluginLifecycleState.ACTIVE,
        )
        assert status.plugin_id == "p1"
        assert status.enabled is True
        assert status.transition_count == 0
        assert status.last_transition_at is None

    def test_immutable(self) -> None:
        status = PluginStatus(
            plugin_id="p1",
            name="Plugin",
            version="1.0.0",
            state=PluginLifecycleState.REGISTERED,
        )
        with pytest.raises(Exception):
            status.state = PluginLifecycleState.ACTIVE  # type: ignore[misc]


# ---------------------------------------------------------------------------
# PluginEventSubscription Model
# ---------------------------------------------------------------------------


class TestPluginEventSubscription:
    def test_construction(self) -> None:
        sub = PluginEventSubscription(
            subscription_id="abc-123",
            event_type=PluginEventType.PLUGIN_ACTIVATED,
            listener_name="my_listener",
        )
        assert sub.subscription_id == "abc-123"
        assert sub.plugin_id is None

    def test_immutable(self) -> None:
        sub = PluginEventSubscription(
            subscription_id="abc-123",
            event_type=PluginEventType.PLUGIN_ACTIVATED,
            listener_name="my_listener",
        )
        with pytest.raises(Exception):
            sub.subscription_id = "other"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# PluginEventDispatcher
# ---------------------------------------------------------------------------


class TestPluginEventDispatcher:
    def test_subscribe_returns_id(self) -> None:
        dispatcher = PluginEventDispatcher()
        listener = MagicMock()
        sub_id = dispatcher.subscribe(PluginEventType.PLUGIN_ACTIVATED, listener, "test_listener")
        assert isinstance(sub_id, str)
        assert len(sub_id) > 0

    def test_dispatch_invokes_listener(self) -> None:
        dispatcher = PluginEventDispatcher()
        received: List[PluginEventPayload] = []
        dispatcher.subscribe(
            PluginEventType.PLUGIN_ACTIVATED, lambda p: received.append(p), "test_listener"
        )
        payload = PluginEventPayload(
            plugin_id="p1",
            event_type=PluginEventType.PLUGIN_ACTIVATED,
            state=PluginLifecycleState.ACTIVE,
        )
        count = dispatcher.dispatch(payload)
        assert count == 1
        assert len(received) == 1
        assert received[0].plugin_id == "p1"

    def test_dispatch_no_listeners_returns_zero(self) -> None:
        dispatcher = PluginEventDispatcher()
        payload = PluginEventPayload(
            plugin_id="p1",
            event_type=PluginEventType.PLUGIN_ACTIVATED,
            state=PluginLifecycleState.ACTIVE,
        )
        count = dispatcher.dispatch(payload)
        assert count == 0

    def test_unsubscribe_removes_listener(self) -> None:
        dispatcher = PluginEventDispatcher()
        received: List[PluginEventPayload] = []
        sub_id = dispatcher.subscribe(
            PluginEventType.PLUGIN_ACTIVATED, lambda p: received.append(p), "test_listener"
        )
        removed = dispatcher.unsubscribe(sub_id)
        assert removed is True
        payload = PluginEventPayload(
            plugin_id="p1",
            event_type=PluginEventType.PLUGIN_ACTIVATED,
            state=PluginLifecycleState.ACTIVE,
        )
        dispatcher.dispatch(payload)
        assert len(received) == 0

    def test_unsubscribe_unknown_returns_false(self) -> None:
        dispatcher = PluginEventDispatcher()
        assert dispatcher.unsubscribe("nonexistent-id") is False

    def test_listener_exception_does_not_stop_others(self) -> None:
        dispatcher = PluginEventDispatcher()
        results: List[str] = []

        def bad_listener(p: PluginEventPayload) -> None:
            raise RuntimeError("boom")

        def good_listener(p: PluginEventPayload) -> None:
            results.append("ok")

        dispatcher.subscribe(PluginEventType.PLUGIN_ACTIVATED, bad_listener, "bad")
        dispatcher.subscribe(PluginEventType.PLUGIN_ACTIVATED, good_listener, "good")

        payload = PluginEventPayload(
            plugin_id="p1",
            event_type=PluginEventType.PLUGIN_ACTIVATED,
            state=PluginLifecycleState.ACTIVE,
        )
        count = dispatcher.dispatch(payload)
        assert count == 1  # only good_listener succeeded
        assert results == ["ok"]

    def test_plugin_id_filter_delivered(self) -> None:
        dispatcher = PluginEventDispatcher()
        received: List[PluginEventPayload] = []
        dispatcher.subscribe(
            PluginEventType.PLUGIN_ACTIVATED,
            lambda p: received.append(p),
            "filtered_listener",
            plugin_id="target-plugin",
        )
        payload = PluginEventPayload(
            plugin_id="target-plugin",
            event_type=PluginEventType.PLUGIN_ACTIVATED,
            state=PluginLifecycleState.ACTIVE,
        )
        dispatcher.dispatch(payload)
        assert len(received) == 1

    def test_plugin_id_filter_skipped(self) -> None:
        dispatcher = PluginEventDispatcher()
        received: List[PluginEventPayload] = []
        dispatcher.subscribe(
            PluginEventType.PLUGIN_ACTIVATED,
            lambda p: received.append(p),
            "filtered_listener",
            plugin_id="target-plugin",
        )
        payload = PluginEventPayload(
            plugin_id="other-plugin",
            event_type=PluginEventType.PLUGIN_ACTIVATED,
            state=PluginLifecycleState.ACTIVE,
        )
        dispatcher.dispatch(payload)
        assert len(received) == 0

    def test_multiple_subscribers_same_event(self) -> None:
        dispatcher = PluginEventDispatcher()
        counts: List[int] = [0]

        def inc(_: PluginEventPayload) -> None:
            counts[0] += 1

        dispatcher.subscribe(PluginEventType.PLUGIN_LOADED, inc, "a")
        dispatcher.subscribe(PluginEventType.PLUGIN_LOADED, inc, "b")
        dispatcher.subscribe(PluginEventType.PLUGIN_LOADED, inc, "c")

        payload = PluginEventPayload(
            plugin_id="p1",
            event_type=PluginEventType.PLUGIN_LOADED,
            state=PluginLifecycleState.LOADED,
        )
        dispatcher.dispatch(payload)
        assert counts[0] == 3

    def test_list_subscriptions(self) -> None:
        dispatcher = PluginEventDispatcher()
        dispatcher.subscribe(PluginEventType.PLUGIN_ACTIVATED, MagicMock(), "l1")
        dispatcher.subscribe(PluginEventType.PLUGIN_LOADED, MagicMock(), "l2")
        subs = dispatcher.list_subscriptions()
        assert len(subs) == 2

    def test_dispatch_state_change_helper(self) -> None:
        dispatcher = PluginEventDispatcher()
        received: List[PluginEventPayload] = []
        dispatcher.subscribe(
            PluginEventType.PLUGIN_ACTIVATED,
            lambda p: received.append(p),
            "helper_listener",
        )
        dispatcher.dispatch_state_change(
            plugin_id="p1",
            new_state=PluginLifecycleState.ACTIVE,
            event_type=PluginEventType.PLUGIN_ACTIVATED,
        )
        assert len(received) == 1
        assert received[0].state == PluginLifecycleState.ACTIVE


# ---------------------------------------------------------------------------
# PluginLifecycleEngine — Registration
# ---------------------------------------------------------------------------


class TestPluginLifecycleEngineRegistration:
    def test_register_sets_registered_state(self) -> None:
        engine = _engine()
        engine.register(_manifest())
        assert engine.get_state("test-plugin") == PluginLifecycleState.REGISTERED

    def test_register_creates_status(self) -> None:
        engine = _engine()
        engine.register(_manifest())
        status = engine.get_status("test-plugin")
        assert status.plugin_id == "test-plugin"
        assert status.state == PluginLifecycleState.REGISTERED

    def test_register_twice_raises(self) -> None:
        engine = _engine()
        engine.register(_manifest())
        with pytest.raises(PluginLifecycleStateError):
            engine.register(_manifest())

    def test_unregister_removes_plugin(self) -> None:
        engine = _engine()
        engine.register(_manifest())
        engine.unregister("test-plugin")
        with pytest.raises(PluginNotFoundError):
            engine.get_state("test-plugin")

    def test_unregister_unknown_raises(self) -> None:
        engine = _engine()
        with pytest.raises(PluginNotFoundError):
            engine.unregister("ghost-plugin")


# ---------------------------------------------------------------------------
# PluginLifecycleEngine — Happy Path Transitions
# ---------------------------------------------------------------------------


class TestPluginLifecycleEngineHappyPath:
    def _engine_with_plugin(self, plugin_id: str = "p1") -> PluginLifecycleEngine:
        engine = _engine()
        engine.register(_manifest(plugin_id))
        return engine

    def test_registered_to_loaded(self) -> None:
        engine = self._engine_with_plugin()
        engine.mark_loaded("p1")
        assert engine.get_state("p1") == PluginLifecycleState.LOADED

    def test_loaded_to_initialized(self) -> None:
        engine = self._engine_with_plugin()
        engine.mark_loaded("p1")
        engine.mark_initialized("p1")
        assert engine.get_state("p1") == PluginLifecycleState.INITIALIZED

    def test_initialized_to_active(self) -> None:
        engine = self._engine_with_plugin()
        engine.mark_loaded("p1")
        engine.mark_initialized("p1")
        engine.mark_active("p1")
        assert engine.get_state("p1") == PluginLifecycleState.ACTIVE

    def test_active_to_suspended(self) -> None:
        engine = self._engine_with_plugin()
        engine.mark_loaded("p1")
        engine.mark_initialized("p1")
        engine.mark_active("p1")
        engine.mark_suspended("p1")
        assert engine.get_state("p1") == PluginLifecycleState.SUSPENDED

    def test_suspended_to_resumed(self) -> None:
        engine = self._engine_with_plugin()
        engine.mark_loaded("p1")
        engine.mark_initialized("p1")
        engine.mark_active("p1")
        engine.mark_suspended("p1")
        engine.mark_resumed("p1")
        assert engine.get_state("p1") == PluginLifecycleState.ACTIVE

    def test_active_to_inactive(self) -> None:
        engine = self._engine_with_plugin()
        engine.mark_loaded("p1")
        engine.mark_initialized("p1")
        engine.mark_active("p1")
        engine.mark_inactive("p1")
        assert engine.get_state("p1") == PluginLifecycleState.INACTIVE

    def test_inactive_to_active(self) -> None:
        engine = self._engine_with_plugin()
        engine.mark_loaded("p1")
        engine.mark_initialized("p1")
        engine.mark_active("p1")
        engine.mark_inactive("p1")
        engine.mark_active("p1")
        assert engine.get_state("p1") == PluginLifecycleState.ACTIVE

    def test_active_to_unloaded(self) -> None:
        engine = self._engine_with_plugin()
        engine.mark_loaded("p1")
        engine.mark_initialized("p1")
        engine.mark_active("p1")
        engine.mark_unloaded("p1")
        assert engine.get_state("p1") == PluginLifecycleState.UNLOADED

    def test_unloaded_to_cleaned_up(self) -> None:
        engine = self._engine_with_plugin()
        engine.mark_loaded("p1")
        engine.mark_initialized("p1")
        engine.mark_active("p1")
        engine.mark_unloaded("p1")
        engine.mark_cleaned_up("p1")
        assert engine.get_state("p1") == PluginLifecycleState.CLEANED_UP

    def test_full_lifecycle_transition_count(self) -> None:
        engine = self._engine_with_plugin()
        engine.mark_loaded("p1")
        engine.mark_initialized("p1")
        engine.mark_active("p1")
        engine.mark_unloaded("p1")
        engine.mark_cleaned_up("p1")
        status = engine.get_status("p1")
        # registration = 1, loaded = 2, initialized = 3, active = 4, unloaded = 5, cleaned_up = 6
        assert status.transition_count == 6


# ---------------------------------------------------------------------------
# PluginLifecycleEngine — Failure Transitions
# ---------------------------------------------------------------------------


class TestPluginLifecycleEngineFailureTransitions:
    def _engine_with_plugin(self, plugin_id: str = "p1") -> PluginLifecycleEngine:
        engine = _engine()
        engine.register(_manifest(plugin_id))
        return engine

    def test_validation_failed(self) -> None:
        engine = self._engine_with_plugin()
        engine.mark_failed("p1", PluginLifecycleState.VALIDATION_FAILED, "bad manifest")
        assert engine.get_state("p1") == PluginLifecycleState.VALIDATION_FAILED

    def test_initialization_failed(self) -> None:
        engine = self._engine_with_plugin()
        engine.mark_loaded("p1")
        engine.mark_failed("p1", PluginLifecycleState.INITIALIZATION_FAILED, "init failed")
        assert engine.get_state("p1") == PluginLifecycleState.INITIALIZATION_FAILED

    def test_activation_failed(self) -> None:
        engine = self._engine_with_plugin()
        engine.mark_loaded("p1")
        engine.mark_initialized("p1")
        engine.mark_failed("p1", PluginLifecycleState.ACTIVATION_FAILED, "cannot activate")
        assert engine.get_state("p1") == PluginLifecycleState.ACTIVATION_FAILED

    def test_error_state_from_active(self) -> None:
        engine = self._engine_with_plugin()
        engine.mark_loaded("p1")
        engine.mark_initialized("p1")
        engine.mark_active("p1")
        engine.mark_failed("p1", PluginLifecycleState.ERROR, "runtime crash")
        assert engine.get_state("p1") == PluginLifecycleState.ERROR

    def test_error_state_carries_error_in_status(self) -> None:
        engine = self._engine_with_plugin()
        engine.mark_loaded("p1")
        engine.mark_initialized("p1")
        engine.mark_active("p1")
        engine.mark_failed("p1", PluginLifecycleState.ERROR, "crash!")
        status = engine.get_status("p1")
        assert status.error_message == "crash!"


# ---------------------------------------------------------------------------
# PluginLifecycleEngine — Invalid Transitions
# ---------------------------------------------------------------------------


class TestPluginLifecycleEngineInvalidTransitions:
    def _engine_with_plugin(self, plugin_id: str = "p1") -> PluginLifecycleEngine:
        engine = _engine()
        engine.register(_manifest(plugin_id))
        return engine

    def test_cannot_jump_registered_to_active(self) -> None:
        engine = self._engine_with_plugin()
        with pytest.raises(PluginInvalidTransitionError):
            engine.transition("p1", PluginLifecycleState.ACTIVE)

    def test_cannot_jump_loaded_to_unregistered(self) -> None:
        engine = self._engine_with_plugin()
        engine.mark_loaded("p1")
        with pytest.raises(PluginInvalidTransitionError):
            engine.transition("p1", PluginLifecycleState.UNREGISTERED)

    def test_cannot_transition_cleaned_up(self) -> None:
        engine = self._engine_with_plugin()
        engine.mark_loaded("p1")
        engine.mark_initialized("p1")
        engine.mark_active("p1")
        engine.mark_unloaded("p1")
        engine.mark_cleaned_up("p1")
        with pytest.raises(PluginInvalidTransitionError):
            engine.transition("p1", PluginLifecycleState.ACTIVE)

    def test_cannot_transition_unknown_plugin(self) -> None:
        engine = _engine()
        with pytest.raises(PluginNotFoundError):
            engine.transition("ghost", PluginLifecycleState.ACTIVE)

    def test_invalid_transition_error_attributes(self) -> None:
        exc = PluginInvalidTransitionError("p1", "ACTIVE", "REGISTERED")
        assert exc.plugin_id == "p1"
        assert exc.from_state == "ACTIVE"
        assert exc.to_state == "REGISTERED"

    def test_invalid_transition_does_not_change_state(self) -> None:
        engine = self._engine_with_plugin()
        try:
            engine.transition("p1", PluginLifecycleState.ACTIVE)
        except PluginInvalidTransitionError:
            pass
        # State must remain REGISTERED, not mutated
        assert engine.get_state("p1") == PluginLifecycleState.REGISTERED


# ---------------------------------------------------------------------------
# PluginLifecycleEngine — History
# ---------------------------------------------------------------------------


class TestPluginLifecycleEngineHistory:
    def _engine_with_plugin(self, plugin_id: str = "p1") -> PluginLifecycleEngine:
        engine = _engine()
        engine.register(_manifest(plugin_id))
        return engine

    def test_initial_history_has_one_entry(self) -> None:
        engine = self._engine_with_plugin()
        history = engine.get_history("p1")
        assert len(history) == 1
        assert history[0].to_state == PluginLifecycleState.REGISTERED

    def test_history_grows_with_transitions(self) -> None:
        engine = self._engine_with_plugin()
        engine.mark_loaded("p1")
        engine.mark_initialized("p1")
        history = engine.get_history("p1")
        assert len(history) == 3

    def test_history_order(self) -> None:
        engine = self._engine_with_plugin()
        engine.mark_loaded("p1")
        history = engine.get_history("p1")
        assert history[0].to_state == PluginLifecycleState.REGISTERED
        assert history[1].to_state == PluginLifecycleState.LOADED

    def test_history_unknown_plugin_raises(self) -> None:
        engine = _engine()
        with pytest.raises(PluginNotFoundError):
            engine.get_history("ghost")


# ---------------------------------------------------------------------------
# PluginLifecycleEngine — Event Dispatch Integration
# ---------------------------------------------------------------------------


class TestPluginLifecycleEngineEventDispatch:
    def test_transition_dispatches_event(self) -> None:
        engine = _engine()
        received: List[PluginEventPayload] = []
        engine.dispatcher.subscribe(
            PluginEventType.PLUGIN_LOADED,
            lambda p: received.append(p),
            "test_listener",
        )
        engine.register(_manifest())
        engine.mark_loaded("test-plugin")
        assert any(p.event_type == PluginEventType.PLUGIN_LOADED for p in received)

    def test_registration_dispatches_registered_event(self) -> None:
        dispatcher = PluginEventDispatcher()
        engine = PluginLifecycleEngine(dispatcher=dispatcher)
        received: List[PluginEventPayload] = []
        dispatcher.subscribe(
            PluginEventType.PLUGIN_REGISTERED,
            lambda p: received.append(p),
            "reg_listener",
        )
        engine.register(_manifest())
        assert len(received) == 1
        assert received[0].plugin_id == "test-plugin"

    def test_error_event_carries_error(self) -> None:
        dispatcher = PluginEventDispatcher()
        engine = PluginLifecycleEngine(dispatcher=dispatcher)
        received: List[PluginEventPayload] = []
        dispatcher.subscribe(
            PluginEventType.PLUGIN_STATE_CHANGED,
            lambda p: received.append(p),
            "err_listener",
        )
        engine.register(_manifest())
        engine.mark_loaded("test-plugin")
        engine.mark_initialized("test-plugin")
        engine.mark_active("test-plugin")
        engine.mark_failed("test-plugin", PluginLifecycleState.ERROR, "fatal")
        error_events = [p for p in received if p.error is not None]
        assert len(error_events) >= 1
        assert error_events[0].error == "fatal"


# ---------------------------------------------------------------------------
# PluginLifecycleEngine — Query API
# ---------------------------------------------------------------------------


class TestPluginLifecycleEngineQueryAPI:
    def test_is_active_true(self) -> None:
        engine = _engine()
        engine.register(_manifest())
        engine.mark_loaded("test-plugin")
        engine.mark_initialized("test-plugin")
        engine.mark_active("test-plugin")
        assert engine.is_active("test-plugin") is True

    def test_is_active_false_when_suspended(self) -> None:
        engine = _engine()
        engine.register(_manifest())
        engine.mark_loaded("test-plugin")
        engine.mark_initialized("test-plugin")
        engine.mark_active("test-plugin")
        engine.mark_suspended("test-plugin")
        assert engine.is_active("test-plugin") is False

    def test_list_all_states_empty(self) -> None:
        engine = _engine()
        assert engine.list_all_states() == {}

    def test_list_all_states_multiple(self) -> None:
        engine = _engine()
        engine.register(_manifest("p1"))
        engine.register(_manifest("p2"))
        states = engine.list_all_states()
        assert "p1" in states
        assert "p2" in states

    def test_get_state_unknown_plugin_raises(self) -> None:
        engine = _engine()
        with pytest.raises(PluginNotFoundError):
            engine.get_state("ghost")

    def test_get_status_unknown_plugin_raises(self) -> None:
        engine = _engine()
        with pytest.raises(PluginNotFoundError):
            engine.get_status("ghost")


# ---------------------------------------------------------------------------
# Phase 2 Exception Hierarchy
# ---------------------------------------------------------------------------


class TestPhase2ExceptionHierarchy:
    def test_lifecycle_error_is_plugin_error(self) -> None:
        from flock.plugins.exceptions import PluginError
        exc = PluginLifecycleError("test")
        assert isinstance(exc, PluginError)

    def test_invalid_transition_is_lifecycle_error(self) -> None:
        exc = PluginInvalidTransitionError("p", "A", "B")
        assert isinstance(exc, PluginLifecycleError)

    def test_lifecycle_state_error_is_lifecycle_error(self) -> None:
        exc = PluginLifecycleStateError("test")
        assert isinstance(exc, PluginLifecycleError)

    def test_event_dispatch_error_is_plugin_error(self) -> None:
        from flock.plugins.exceptions import PluginError
        exc = PluginEventDispatchError("test")
        assert isinstance(exc, PluginError)


# ---------------------------------------------------------------------------
# Public __init__ exports
# ---------------------------------------------------------------------------


class TestPublicExports:
    def test_all_phase2_symbols_exported(self) -> None:
        import flock.plugins as pkg
        phase2_symbols = [
            "PluginLifecycleState",
            "PluginEventType",
            "PluginLifecycleTransition",
            "PluginEventPayload",
            "PluginStatus",
            "PluginEventSubscription",
            "PluginEventDispatcher",
            "PluginLifecycleEngine",
            "PluginLifecycleError",
            "PluginInvalidTransitionError",
            "PluginEventDispatchError",
            "PluginLifecycleStateError",
        ]
        for sym in phase2_symbols:
            assert hasattr(pkg, sym), f"Missing export: {sym}"

    def test_phase1_symbols_still_exported(self) -> None:
        import flock.plugins as pkg
        phase1_symbols = [
            "PluginManifest", "PluginRegistry", "PluginLoader",
            "FlockPlugin", "PluginService", "PluginValidator",
            "PluginDiscovery",
        ]
        for sym in phase1_symbols:
            assert hasattr(pkg, sym), f"Phase 1 export missing: {sym}"
