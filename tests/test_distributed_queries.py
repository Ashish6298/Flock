"""Unit tests for DistributedQueries."""

from flock.query.models import ExecutionPlan, ExecutionStage
from flock.query.executor import QueryExecutor


def test_distributed_query_execution_matching() -> None:
    executor = QueryExecutor()
    stages = [
        ExecutionStage(stage_id="s1", operation_type="SCAN", properties={"table": "users"}),
    ]
    plan = ExecutionPlan(stages=stages)

    dataset = {
        "users": [
            [1, "Alice"],
            [2, "Bob"],
        ]
    }
    cols = ["id", "name"]

    res = executor.execute_plan(plan, dataset, cols)
    assert res.success is True
    assert len(res.rows) == 2
