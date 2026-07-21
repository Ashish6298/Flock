"""Aggregation Engine processing SQL aggregates and GROUP BYs."""

from __future__ import annotations

from typing import Any, Dict, List

from flock.query.exceptions import InvalidAggregationError
from flock.query.models import AggregationResult


class AggregationEngine:
    """Evaluates aggregate functions COUNT, SUM, AVG, MIN, MAX."""

    def __init__(self) -> None:
        pass

    def compute_aggregates(self, rows: List[List[Any]], agg_column_idx: int, func_type: str) -> float:
        """Compute values matching COUNT, SUM, or AVG.

        Raises:
            InvalidAggregationError: If target function type is unsupported.
        """
        if not rows:
            return 0.0

        vals = [float(row[agg_column_idx]) for row in rows if row[agg_column_idx] is not None]
        if not vals and func_type != "COUNT":
            return 0.0

        op = func_type.upper()
        if op == "COUNT":
            return float(len(rows))
        elif op == "SUM":
            return sum(vals)
        elif op == "AVG":
            return sum(vals) / len(vals) if vals else 0.0
        elif op == "MIN":
            return min(vals) if vals else 0.0
        elif op == "MAX":
            return max(vals) if vals else 0.0
        else:
            raise InvalidAggregationError(f"Unsupported aggregate function: '{func_type}'")
