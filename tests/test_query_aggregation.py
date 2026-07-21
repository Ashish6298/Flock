"""Unit tests for AggregationEngine."""

import pytest
from flock.query.aggregation import AggregationEngine
from flock.query.exceptions import InvalidAggregationError


def test_aggregate_reductions() -> None:
    engine = AggregationEngine()
    rows = [
        [1, 10.0],
        [2, 20.0],
        [3, 30.0],
    ]

    assert engine.compute_aggregates(rows, agg_column_idx=1, func_type="SUM") == 60.0
    assert engine.compute_aggregates(rows, agg_column_idx=1, func_type="AVG") == 20.0
    assert engine.compute_aggregates(rows, agg_column_idx=1, func_type="COUNT") == 3.0

    # Unsupported aggregate throws InvalidAggregationError
    with pytest.raises(InvalidAggregationError):
        engine.compute_aggregates(rows, agg_column_idx=1, func_type="BAD_OP")
