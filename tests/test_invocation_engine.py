"""Unit tests for InvocationEngine."""

import pytest
from flock.functions.exceptions import InvocationFailedError
from flock.functions.invocation import InvocationEngine
from flock.functions.models import FunctionDefinition, InvocationRequest
from flock.functions.registry import FunctionRegistry
from flock.functions.runtime import RuntimeEngine


def test_invocation_routing_calls_runtime() -> None:
    registry = FunctionRegistry()
    runtime = RuntimeEngine()
    invoker = InvocationEngine(registry, runtime)

    func = FunctionDefinition(
        function_id="f1",
        name="say-hi",
        handler_code="def handler(): return 'hi'",
    )
    registry.register_function(func)

    req = InvocationRequest(invocation_id="i1", function_id="f1")
    res = invoker.invoke(req)
    assert res.success is True
    assert res.output == "hi"

    req_missing = InvocationRequest(invocation_id="i2", function_id="missing")
    with pytest.raises(InvocationFailedError):
        invoker.invoke(req_missing)
