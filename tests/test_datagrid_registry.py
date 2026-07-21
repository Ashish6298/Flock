"""Unit tests for DataGridRegistry."""

from flock.datagrid.models import BucketDefinition, CollectionDefinition
from flock.datagrid.registry import DataGridRegistry


def test_registry_add_and_list() -> None:
    registry = DataGridRegistry()
    col = CollectionDefinition(name="users")
    bucket = BucketDefinition(bucket_name="images", quota_limit=500)

    registry.register_collection(col)
    registry.register_bucket(bucket)

    assert registry.get_collection("users") == col
    assert registry.get_bucket("images") == bucket
    assert len(registry.list_collections()) == 1
