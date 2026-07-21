"""Unit tests for QueryOptimizer."""

from flock.query.models import ExecutionPlan, ExecutionStage
from flock.query.optimizer import QueryOptimizer


def test_optimizer_predicate_pushdown() -> None:
    optimizer = QueryOptimizer()

    stages = [
        ExecutionStage(stage_id="s1", operation_type="SCAN", properties={"table": "users"}),
        ExecutionStage(stage_id="s2", operation_type="PROJECTION", properties={"columns": ["name"]}),
        ExecutionStage(stage_id="s3", operation_type="FILTER", properties={"expression": "status = 'active'"}),
    ]
    plan = ExecutionPlan(stages=stages)

    opt = optimizer.optimize_plan(plan)
    
    # Filter stage is pushed down directly after Scan
    assert opt.stages[0].operation_type == "SCAN"
    assert opt.stages[1].operation_type == "FILTER"
    assert opt.stages[2].operation_type == "PROJECTION"
