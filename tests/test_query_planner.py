"""Unit tests for QueryPlanner."""

import pytest
from flock.query.exceptions import QueryPlannerError
from flock.query.planner import QueryPlanner


def test_planner_builds_stages() -> None:
    planner = QueryPlanner()
    ast = {
        "projections": ["name"],
        "table": "users",
        "filter": "status = 'active'",
        "group_by": ["status"],
    }

    plan = planner.build_plan(ast)
    assert len(plan.stages) == 4
    assert plan.stages[0].operation_type == "SCAN"
    assert plan.stages[1].operation_type == "FILTER"
    assert plan.stages[2].operation_type == "AGGREGATE"
    assert plan.stages[3].operation_type == "PROJECTION"


def test_planner_missing_table_raises() -> None:
    planner = QueryPlanner()
    with pytest.raises(QueryPlannerError):
        planner.build_plan({"projections": ["*"]})
