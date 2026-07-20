"""Event Trigger Engine evaluating incoming EventBus patterns."""

from __future__ import annotations

from typing import Dict, List

from flock.events.bus import EventBus
from flock.scheduling.models import EventTrigger


class EventTriggerEngine:
    """Evaluates local and global EventBus notifications against triggers catalog."""

    def __init__(self, event_bus: EventBus) -> None:
        self._events = event_bus
        self._triggers: Dict[str, EventTrigger] = {}

    def register_trigger(self, trigger: EventTrigger) -> None:
        """Register an event-driven automation trigger."""
        self._triggers[trigger.trigger_id] = trigger

    def match_event(self, event_type: str) -> List[EventTrigger]:
        """Find triggers matching matching event categories."""
        matched: List[EventTrigger] = []
        for t in self._triggers.values():
            if t.event_pattern == event_type:
                matched.append(t)
        return matched
