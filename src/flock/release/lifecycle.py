"""Subsystem lifecycle state updates coordinator."""

from __future__ import annotations

import threading
from typing import Dict, List, Optional
from flock.release.exceptions import SubsystemLifecycleError
from flock.release.models import SubsystemStatus


class SubsystemLifecycleCoordinator:
    """Manages active registration and states mapping for all subsystems."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        # name -> SubsystemStatus
        self._states: Dict[str, SubsystemStatus] = {}

    def register_subsystem(self, name: str) -> None:
        """Register subsystem under lifecycle tracking."""
        with self._lock:
            self._states[name] = SubsystemStatus(name=name, state="uninitialized", errors=[])

    def set_subsystem_state(self, name: str, state: str, errors: Optional[List[str]] = None) -> None:
        """Update lifecycle state of registered subsystem.
        
        Raises:
            SubsystemLifecycleError: If subsystem is not registered.
        """
        with self._lock:
            if name not in self._states:
                raise SubsystemLifecycleError(f"Subsystem '{name}' is not registered under lifecycle coordinator.")
            self._states[name] = SubsystemStatus(name=name, state=state, errors=errors or [])

    def get_subsystem_status(self, name: str) -> SubsystemStatus:
        with self._lock:
            if name not in self._states:
                raise SubsystemLifecycleError(f"Subsystem '{name}' is not registered.")
            return self._states[name]

    def list_subsystems(self) -> List[SubsystemStatus]:
        with self._lock:
            return list(self._states.values())
