"""Circuit Breaker Engine tracking call failure bounds."""

from __future__ import annotations

import threading
import time
from typing import Dict

from flock.mesh.exceptions import CircuitBreakerOpenError
from flock.mesh.models import CircuitBreaker


class CircuitBreakerEngine:
    """Manages active, half-open, and tripped states for service boundaries."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        
        # service_id -> fail_count
        self._failures: Dict[str, int] = {}
        # service_id -> cooldown_expiry_timestamp
        self._tripped_until: Dict[str, float] = {}

    def record_success(self, service_id: str) -> None:
        """Reset failures count on successful connection."""
        with self._lock:
            self._failures[service_id] = 0
            self._tripped_until.pop(service_id, None)

    def record_failure(self, service_id: str, config: CircuitBreaker) -> None:
        """Increment failure logs. Trip breaker if threshold is exceeded."""
        with self._lock:
            count = self._failures.get(service_id, 0) + 1
            self._failures[service_id] = count

            if count >= config.max_failures:
                self._tripped_until[service_id] = time.time() + config.cooldown

    def check_call_allowed(self, service_id: str) -> None:
        """Validate if service execution is allowed.

        Raises:
            CircuitBreakerOpenError: If breaker is tripped and cooldown has not expired.
        """
        with self._lock:
            expiry = self._tripped_until.get(service_id)
            if expiry:
                if time.time() < expiry:
                    raise CircuitBreakerOpenError(
                        f"Circuit breaker for service '{service_id}' is open. Request blocked."
                    )
                # Cooldown expired, transition to half-open
                self._tripped_until.pop(service_id, None)
