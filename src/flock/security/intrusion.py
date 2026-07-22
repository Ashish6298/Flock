"""Suspicious behavior tracking, authentication failure thresholds, and threat identification heuristics."""

from __future__ import annotations

import time
import threading
from typing import Any, Dict, List, Set, Optional
from flock.security.exceptions import IntrusionDetectionAlert


class IntrusionDetector:
    """Monitors security events for attack indicators (brute-force, port-scans)."""

    def __init__(self, failure_threshold: int = 5, window_seconds: float = 60.0) -> None:
        self._lock = threading.RLock()
        self._failure_threshold = failure_threshold
        self._window_seconds = window_seconds
        
        # subject -> list of timestamps of failures
        self._auth_failures: Dict[str, List[float]] = {}
        # Blacklisted subjects
        self._blacklist: Set[str] = set()
        # Incident history list
        self._threat_incidents: List[Dict[str, Any]] = []

    def record_auth_failure(self, subject: str) -> bool:
        """Record a failed auth attempt. Returns True if a threshold is breached (attack match)."""
        now = time.time()
        with self._lock:
            if subject in self._blacklist:
                return True
                
            failures = self._auth_failures.setdefault(subject, [])
            failures.append(now)
            
            # Prune old failures outside time window
            cutoff = now - self._window_seconds
            failures = [t for t in failures if t >= cutoff]
            self._auth_failures[subject] = failures
            
            if len(failures) >= self._failure_threshold:
                self._blacklist.add(subject)
                incident = {
                    "subject": subject,
                    "reason": "Brute-force authentication attempts detected",
                    "failures_count": len(failures),
                    "timestamp": now,
                }
                self._threat_incidents.append(incident)
                return True
                
            return False

    def is_blacklisted(self, subject: str) -> bool:
        """Check if subject is currently blacklisted due to security breach rules."""
        with self._lock:
            return subject in self._blacklist

    def remove_from_blacklist(self, subject: str) -> None:
        """Remove subject from blacklist."""
        with self._lock:
            self._blacklist.discard(subject)
            self._auth_failures.pop(subject, None)

    def get_blacklist(self) -> List[str]:
        """Return a list of blacklisted subject identifiers."""
        with self._lock:
            return list(self._blacklist)

    def list_incidents(self) -> List[Dict[str, Any]]:
        """Return the history list of matching threat incidents."""
        with self._lock:
            return list(self._threat_incidents)
