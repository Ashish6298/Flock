"""Trigger Engine matching EventBus changes to target handlers."""

from __future__ import annotations

import threading
from typing import Dict, List

from flock.functions.exceptions import TriggerSyncError
from flock.functions.models import TriggerDefinition


class TriggerEngine:
    """Matches EventBus changes to execution triggers."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        
        # trigger_id -> TriggerDefinition
        self._triggers: Dict[str, TriggerDefinition] = {}

    def register_trigger(self, trigger: TriggerDefinition) -> None:
        """Register dynamic trigger definition mapping."""
        with self._lock:
            self._triggers[trigger.trigger_id] = trigger

    def match_triggers(self, source: str) -> List[TriggerDefinition]:
        """Find registered triggers matching event coordinates."""
        with self._lock:
            return [t for t in self._triggers.values() if t.source == source]
