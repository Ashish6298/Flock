"""Unit tests for SnapshotStorage."""

import time
import pytest
from flock.snapshot.exceptions import SnapshotChecksumError
from flock.snapshot.models import SnapshotMetadata
from flock.snapshot.storage import SnapshotStorage


def test_storage_save_and_retrieve() -> None:
    storage = SnapshotStorage()
    data = b'{"state": {"key": "val"}}'
    checksum = "8c66e2c431b9a9572ec56b063d33db864c39f0460a8b9fdfb744002cbbbaaa0f"
    # Actually calculate real SHA256 of data
    import hashlib
    checksum = hashlib.sha256(data).hexdigest()
    
    metadata = SnapshotMetadata(
        snapshot_id="snap-1",
        applied_index=5,
        current_term=1,
        timestamp=time.time(),
        checksum=checksum,
        size_bytes=len(data),
    )

    storage.save_snapshot(metadata, data)
    assert len(storage.list_snapshots()) == 1

    fetched = storage.get_snapshot("snap-1")
    assert fetched is not None
    assert fetched[0].applied_index == 5
    assert fetched[1] == data


def test_storage_invalid_checksum_raises() -> None:
    storage = SnapshotStorage()
    data = b"corrupted payload"
    metadata = SnapshotMetadata(
        snapshot_id="snap-2",
        applied_index=5,
        current_term=1,
        timestamp=time.time(),
        checksum="invalid_checksum",
        size_bytes=len(data),
    )

    with pytest.raises(SnapshotChecksumError):
        storage.save_snapshot(metadata, data)


def test_storage_retention_policy() -> None:
    # Max snapshots is 2
    storage = SnapshotStorage(max_snapshots=2)
    import hashlib
    
    for i in range(1, 4):
        data = f"data-{i}".encode("utf-8")
        checksum = hashlib.sha256(data).hexdigest()
        metadata = SnapshotMetadata(
            snapshot_id=f"snap-{i}",
            applied_index=i,
            current_term=1,
            timestamp=time.time(),
            checksum=checksum,
            size_bytes=len(data),
        )
        storage.save_snapshot(metadata, data)

    # First snapshot (snap-1) should have been pruned due to retention policy limit of 2
    snapshots = storage.list_snapshots()
    assert len(snapshots) == 2
    assert snapshots[0].snapshot_id == "snap-2"
    assert snapshots[1].snapshot_id == "snap-3"
