"""Unit tests for KeyValueEngine."""

import pytest
from flock.datagrid.exceptions import RecordNotFoundError
from flock.datagrid.kvstore import KeyValueEngine


def test_kv_store_transactions() -> None:
    engine = KeyValueEngine()

    # Basic put and get updates revision versions
    rec = engine.put("k1", "val-1")
    assert rec.version == 1
    assert engine.get("k1").value == "val-1"

    rec2 = engine.put("k1", "val-2")
    assert rec2.version == 2

    # Compare-And-Swap modifies when version matches
    assert engine.compare_and_swap("k1", expected_version=2, new_value="val-cas") is True
    assert engine.get("k1").value == "val-cas"

    # Compare-And-Swap fails if version differs
    assert engine.compare_and_swap("k1", expected_version=100, new_value="val-bad") is False

    # Delete clears registry
    engine.delete("k1")
    with pytest.raises(RecordNotFoundError):
        engine.get("k1")
