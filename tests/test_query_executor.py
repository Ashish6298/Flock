"""Unit tests for QueryExecutor."""

import pytest
from flock.query.exceptions import QueryExecutionError
from flock.query.executor import QueryExecutor
from flock.query.models import ExecutionPlan, ExecutionStage


def test_executor_scans_and_filters() -> None:
    executor = QueryExecutor()
    stages = [
        ExecutionStage(stage_id="s1", operation_type="SCAN", properties={"table": "users"}),
        ExecutionStage(stage_id="s2", operation_type="FILTER", properties={"expression": "status = 'active'"}),
    ]
    plan = ExecutionPlan(stages=stages)

    dataset = {
        "users": [
            [1, "Alice", "active"],
            [2, "Bob", "inactive"],
        ]
    }
    cols = ["id", "name", "status"]

    res = executor.execute_plan(plan, dataset, cols)
    assert res.success is True
    # Alice is active, Bob is filtered out
    assert len(res.rows) == 1
    assert res.rows[0][1] == "Alice"


def test_executor_missing_table_raises() -> None:
    executor = QueryExecutor()
    stages = [
        ExecutionStage(stage_id="s1", operation_type="SCAN", properties={"table": "missing"}),
    ]
    plan = ExecutionPlan(stages=stages)
    with pytest.raises(QueryExecutionError):
        executor.execute_plan(plan, {}, [])
