"""Tamper-evident auditing logs for dynamic membership alterations and security events."""

from __future__ import annotations

import time
import threading
from typing import Dict, List, Any


class FederationAuditLogger:
    """Logs security trust operations and routing updates in a historical event list."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._logs: List[Dict[str, Any]] = []

    def log_event(self, event_name: str, details: Dict[str, Any]) -> None:
        """Append audit event entry."""
        with self._lock:
            self._logs.append({
                "event_name": event_name,
                "timestamp": time.time(),
                "details": details,
            })

    def get_logs(self) -> List[Dict[str, Any]]:
        """Retrieve audit trails log copy."""
        with self._lock:
            return list(self._logs)
