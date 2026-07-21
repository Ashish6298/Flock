"""Unit tests for DataGridMetrics."""

from flock.datagrid.models import BucketDefinition


def test_bucket_metrics_values() -> None:
    bucket = BucketDefinition(
        bucket_name="metrics-bucket",
        quota_limit=2048,
    )

    assert bucket.bucket_name == "metrics-bucket"
    assert bucket.quota_limit == 2048
