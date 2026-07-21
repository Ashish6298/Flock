"""Unit tests for QueryStatistics."""

from flock.query.models import ExecutionStatistics


def test_statistics_values() -> None:
    stats = ExecutionStatistics(
        rows_processed=1000,
        execution_time_ms=45.2,
    )

    assert stats.rows_processed == 1000
    assert stats.execution_time_ms == 45.2
