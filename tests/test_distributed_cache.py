"""Unit tests for DistributedCacheEngine."""

import time
from flock.datagrid.cache import DistributedCacheEngine


def test_cache_expiration_lifecycle() -> None:
    engine = DistributedCacheEngine()

    # Immediate access works
    engine.put("cache-1", "temp-val", ttl_seconds=10)
    assert engine.get("cache-1") == "temp-val"

    # Expired access returns None
    engine.put("cache-expired", "old-val", ttl_seconds=-1)
    assert engine.get("cache-expired") is None

    # Delete clears entry
    engine.put("cache-delete", "val")
    engine.delete("cache-delete")
    assert engine.get("cache-delete") is None
