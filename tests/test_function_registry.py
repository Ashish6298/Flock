"""Unit tests for FunctionRegistry."""

import pytest
from flock.functions.exceptions import FunctionNotFoundError
from flock.functions.models import FunctionDefinition
from flock.functions.registry import FunctionRegistry


def test_registry_add_and_list() -> None:
    registry = FunctionRegistry()
    func = FunctionDefinition(
        function_id="func-1",
        name="hello-world",
        handler_code="def handler(): return 'hello'",
    )

    registry.register_function(func)
    assert registry.get_function("func-1") == func
    assert len(registry.list_functions()) == 1

    registry.unregister_function("func-1")
    with pytest.raises(FunctionNotFoundError):
        registry.get_function("func-1")
