"""Unit tests for CircuitBreakerEngine."""

import pytest
from flock.mesh.breaker import CircuitBreakerEngine
from flock.mesh.exceptions import CircuitBreakerOpenError
from flock.mesh.models import CircuitBreaker


def test_breaker_tripping_lifecycle() -> None:
    engine = CircuitBreakerEngine()
    config = CircuitBreaker(service_id="service-1", max_failures=2, cooldown=0.5)

    # Initial call allowed
    engine.check_call_allowed("service-1")

    # Record 1st failure
    engine.record_failure("service-1", config)
    engine.check_call_allowed("service-1")

    # Record 2nd failure -> trips breaker
    engine.record_failure("service-1", config)
    with pytest.raises(CircuitBreakerOpenError):
        engine.check_call_allowed("service-1")
