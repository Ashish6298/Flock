"""Unit tests for RuntimeEngine."""

from flock.functions.models import FunctionDefinition, InvocationRequest
from flock.functions.runtime import RuntimeEngine


def test_runtime_executes_handler() -> None:
    engine = RuntimeEngine()
    
    # Valid handler execution runs successfully
    func = FunctionDefinition(
        function_id="f1",
        name="add",
        handler_code="def handler(x, y): return x + y",
    )
    req = InvocationRequest(invocation_id="i1", function_id="f1", args=[5, 10])
    
    res = engine.execute_handler(func, req)
    assert res.success is True
    assert res.output == 15

    # Handler code with syntax error returns failure result
    func_bad = FunctionDefinition(
        function_id="f2",
        name="syntax-err",
        handler_code="def handler(): syntax error here",
    )
    req_bad = InvocationRequest(invocation_id="i2", function_id="f2")
    res_bad = engine.execute_handler(func_bad, req_bad)
    assert res_bad.success is False
    assert res_bad.error is not None
