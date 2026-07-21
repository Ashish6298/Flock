"""Unit tests for DistributedLockManager."""

import pytest
from flock.datagrid.exceptions import LockAcquisitionError
from flock.datagrid.locking import DistributedLockManager


def test_lock_acquires_leases() -> None:
    manager = DistributedLockManager()

    # Lock acquires successfully
    lease = manager.acquire_lock("resource-1", lease_seconds=10)
    assert lease.lock_key == "resource-1"

    # Conflicting lock acquisition throws LockAcquisitionError
    with pytest.raises(LockAcquisitionError):
        manager.acquire_lock("resource-1", lease_seconds=5)

    manager.release_lock("resource-1", lease.lease_id)
    lease2 = manager.acquire_lock("resource-1", lease_seconds=5)
    assert lease2.lease_id != lease.lease_id
