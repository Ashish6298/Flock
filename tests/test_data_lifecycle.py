"""Unit tests for DataLifecycleManager."""

import time
from flock.datagrid.lifecycle import DataLifecycleManager


def test_lifecycle_TTL_evaluations() -> None:
    manager = DataLifecycleManager()

    # Key under TTL limit is not expired
    manager.set_expiration("k1", ttl_seconds=10.0)
    assert len(manager.evaluate_expired_keys()) == 0

    # Key exceeding TTL limit is returned as expired
    manager.set_expiration("k2", ttl_seconds=-1.0)
    assert manager.evaluate_expired_keys() == {"k2"}
