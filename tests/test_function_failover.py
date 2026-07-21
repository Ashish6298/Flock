"""Unit tests for FunctionFailover."""

import pytest
from flock.functions.exceptions import InvocationFailedError
from flock.functions.invocation import InvocationEngine
from flock.functions.models import InvocationRequest
from flock.functions.registry import FunctionRegistry
from flock.functions.runtime import RuntimeEngine


def test_failover_when_registry_is_missing() -> None:
    registry = FunctionRegistry()
    runtime = RuntimeEngine()
    invoker = InvocationEngine(registry, runtime)

    req = InvocationRequest(invocation_id="i-fail", function_id="nonexistent-func")
    with pytest.raises(InvocationFailedError):
        invoker.invoke(req)
