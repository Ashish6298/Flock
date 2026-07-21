"""Unit tests for DataGridFailover."""

import pytest
from flock.datagrid.exceptions import RecordNotFoundError
from flock.datagrid.kvstore import KeyValueEngine


def test_kv_store_lookup_missing_key_failover() -> None:
    engine = KeyValueEngine()

    # Look up non-existent key throws RecordNotFoundError
    with pytest.raises(RecordNotFoundError):
        engine.get("nonexistent-key")
