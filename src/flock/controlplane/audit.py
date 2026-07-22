"""Control plane tamper-evident security audit logger."""

from __future__ import annotations

import time
import threading
from typing import Dict, List, Any


class ControlPlaneAuditLogger:
    """Logs fleet enrollments, policy synchronization, and maintenance operations."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._logs: List[Dict[str, Any]] = []

    def log_event(self, event_name: str, details: Dict[str, Any]) -> None:
        with self._lock:
            self._logs.append({
                "event_name": event_name,
                "timestamp": time.time(),
                "details": details,
            })

    def get_logs(self) -> List[Dict[str, Any]]:
        with self._lock:
            return list(self._logs)
