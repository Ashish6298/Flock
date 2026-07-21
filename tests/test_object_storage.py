"""Unit tests for ObjectStorageEngine."""

import pytest
from flock.datagrid.exceptions import BucketQuotaExceededError
from flock.datagrid.objectstore import ObjectStorageEngine


def test_object_storage_uploads() -> None:
    engine = ObjectStorageEngine(size_limit=10)

    # Valid payload size uploads successfully
    rec = engine.upload_object("obj-1", b"short")
    assert rec.object_key == "obj-1"
    assert engine.download_object("obj-1") == b"short"

    # Excess payload size throws BucketQuotaExceededError
    with pytest.raises(BucketQuotaExceededError):
        engine.upload_object("obj-2", b"very-long-payload-exceeding-limit")
