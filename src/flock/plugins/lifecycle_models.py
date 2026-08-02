"""Plugin Lifecycle & Event System Models.

Defines strongly typed Pydantic v2 models for plugin lifecycle states,
lifecycle events, event payloads, event subscriptions, transition records,
and plugin status information used throughout Milestone E Phase 2.
"""

from __future__ import annotations

import time
from enum import Enum
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Lifecycle State Enumeration
# ---------------------------------------------------------------------------


class PluginLifecycleState(str, Enum):
    """Enumeration of all valid plugin lifecycle states.

    State Machine Diagram::

        UNREGISTERED
             |
          register
             v
        REGISTERED ─── validate_fail ──► VALIDATION_FAILED
             |
          validate_ok
             v
          LOADED ──── initialize_fail ──► INITIALIZATION_FAILED
             |
          initialize_ok
             v
        INITIALIZED ──── activate_fail ──► ACTIVATION_FAILED
             |
          activate
             v
          ACTIVE
             |
         ┌───┴──────┐
       suspend    deactivate
         v            v
      SUSPENDED    INACTIVE
         |
       resume
         v
        ACTIVE
             |
          unload
             v
        UNLOADED ─── cleanup ──► CLEANED_UP
    """

    UNREGISTERED = "UNREGISTERED"
    REGISTERED = "REGISTERED"
    VALIDATION_FAILED = "VALIDATION_FAILED"
    LOADED = "LOADED"
    INITIALIZATION_FAILED = "INITIALIZATION_FAILED"
    INITIALIZED = "INITIALIZED"
    ACTIVATION_FAILED = "ACTIVATION_FAILED"
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    INACTIVE = "INACTIVE"
    UNLOADED = "UNLOADED"
    CLEANED_UP = "CLEANED_UP"
    ERROR = "ERROR"


# ---------------------------------------------------------------------------
# Lifecycle Event Type Enumeration
# ---------------------------------------------------------------------------


class PluginEventType(str, Enum):
    """Enumeration of all plugin lifecycle event types dispatched by the engine."""

    PLUGIN_REGISTERED = "plugin.registered"
    PLUGIN_UNREGISTERED = "plugin.unregistered"
    PLUGIN_LOADED = "plugin.loaded"
    PLUGIN_INITIALIZED = "plugin.initialized"
    PLUGIN_ACTIVATED = "plugin.activated"
    PLUGIN_DEACTIVATED = "plugin.deactivated"
    PLUGIN_SUSPENDED = "plugin.suspended"
    PLUGIN_RESUMED = "plugin.resumed"
    PLUGIN_UNLOADED = "plugin.unloaded"
    PLUGIN_CLEANED_UP = "plugin.cleaned_up"
    PLUGIN_FAILED = "plugin.failed"
    PLUGIN_STATE_CHANGED = "plugin.state_changed"


# ---------------------------------------------------------------------------
# Lifecycle Transition Records
# ---------------------------------------------------------------------------


class PluginLifecycleTransition(BaseModel):
    """Immutable record of a single lifecycle state transition."""

    plugin_id: str = Field(..., description="Unique plugin identifier.")
    from_state: PluginLifecycleState = Field(..., description="State before transition.")
    to_state: PluginLifecycleState = Field(..., description="State after transition.")
    event_type: PluginEventType = Field(..., description="Event that triggered the transition.")
    timestamp: float = Field(default_factory=time.time, description="Unix timestamp of the transition.")
    message: Optional[str] = Field(None, description="Optional human-readable description.")
    error: Optional[str] = Field(None, description="Optional error message if transition failed.")

    model_config = {"frozen": True}


# ---------------------------------------------------------------------------
# Plugin Event Payload
# ---------------------------------------------------------------------------


class PluginEventPayload(BaseModel):
    """Structured payload carried by a dispatched plugin lifecycle event."""

    plugin_id: str = Field(..., description="Unique plugin identifier.")
    event_type: PluginEventType = Field(..., description="The event type.")
    state: PluginLifecycleState = Field(..., description="Current lifecycle state at event time.")
    timestamp: float = Field(default_factory=time.time, description="Unix timestamp of the event.")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Optional key-value metadata.")
    error: Optional[str] = Field(None, description="Error detail if this is a failure event.")

    model_config = {"frozen": True, "arbitrary_types_allowed": True}


# ---------------------------------------------------------------------------
# Plugin Status Snapshot
# ---------------------------------------------------------------------------


class PluginStatus(BaseModel):
    """Point-in-time snapshot of a plugin's current lifecycle status."""

    plugin_id: str = Field(..., description="Unique plugin identifier.")
    name: str = Field(..., description="Human-readable plugin name.")
    version: str = Field(..., description="Plugin version string.")
    state: PluginLifecycleState = Field(..., description="Current lifecycle state.")
    enabled: bool = Field(default=True, description="Whether the plugin is administratively enabled.")
    registered_at: float = Field(default_factory=time.time, description="Unix timestamp of registration.")
    last_transition_at: Optional[float] = Field(None, description="Unix timestamp of last state change.")
    transition_count: int = Field(default=0, description="Total number of state transitions recorded.")
    error_message: Optional[str] = Field(None, description="Last error message, if any.")

    model_config = {"frozen": True}


# ---------------------------------------------------------------------------
# Event Subscription Record
# ---------------------------------------------------------------------------


class PluginEventSubscription(BaseModel):
    """Immutable record representing a listener's subscription to a plugin event type."""

    subscription_id: str = Field(..., description="Unique subscription identifier.")
    event_type: PluginEventType = Field(..., description="Event type being subscribed to.")
    listener_name: str = Field(..., description="Descriptive name of the subscribing listener.")
    plugin_id: Optional[str] = Field(
        None, description="If set, only events from this plugin_id are delivered."
    )
    created_at: float = Field(default_factory=time.time, description="Unix timestamp of subscription creation.")

    model_config = {"frozen": True}
