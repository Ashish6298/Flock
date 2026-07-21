"""Unit tests for FunctionVersionManager."""

import pytest
from flock.functions.exceptions import FunctionValidationError
from flock.functions.versioning import FunctionVersionManager


def test_version_split_routing() -> None:
    manager = FunctionVersionManager()
    splits = {"v1": 30.0, "v2": 70.0}

    # Choice matches splits values
    selected = set()
    for _ in range(100):
        selected.add(manager.resolve_version_route(splits))
    assert "v1" in selected or "v2" in selected


def test_invalid_splits_raises() -> None:
    manager = FunctionVersionManager()
    
    # Empty split mapping throws FunctionValidationError
    with pytest.raises(FunctionValidationError):
        manager.resolve_version_route({})

    with pytest.raises(FunctionValidationError):
        manager.resolve_version_route({"v1": 10.0, "v2": 20.0})
