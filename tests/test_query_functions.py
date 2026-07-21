"""Unit tests for QueryFunctionRegistry."""

import pytest
from flock.query.exceptions import FunctionNotFoundError
from flock.query.functions import QueryFunctionRegistry


def test_builtins_evaluation() -> None:
    registry = QueryFunctionRegistry()

    assert registry.execute_function("abs", -15.5) == 15.5
    assert registry.execute_function("upper", "hello") == "HELLO"

    # Mismatched arity throws ValueError
    with pytest.raises(ValueError):
        registry.execute_function("upper", "hello", "extra-arg")

    # Unregistered function throws FunctionNotFoundError
    with pytest.raises(FunctionNotFoundError):
        registry.execute_function("missing_func", 1)
