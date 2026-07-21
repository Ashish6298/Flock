"""Query Planner converting ASTs to ExecutionPlans."""

from __future__ import annotations

from typing import Any, Dict

from flock.query.exceptions import QueryPlannerError
from flock.query.models import ExecutionPlan, ExecutionStage


class QueryPlanner:
    """Computes logical physical stages paths."""

    def __init__(self) -> None:
        pass

    def build_plan(self, ast: Dict[str, Any]) -> ExecutionPlan:
        """Create sequential execution plan stages from parsed AST.

        Raises:
            QueryPlannerError: If target query specifications are invalid.
        """
        table = ast.get("table")
        if not table:
            raise QueryPlannerError("Table specifier is missing from query AST.")

        stages = []
        stages.append(
            ExecutionStage(
                stage_id="stage-scan",
                operation_type="SCAN",
                properties={"table": table},
            )
        )

        filter_expr = ast.get("filter")
        if filter_expr:
            stages.append(
                ExecutionStage(
                    stage_id="stage-filter",
                    operation_type="FILTER",
                    properties={"expression": filter_expr},
                )
            )

        group_by = ast.get("group_by")
        if group_by:
            stages.append(
                ExecutionStage(
                    stage_id="stage-aggregate",
                    operation_type="AGGREGATE",
                    properties={"keys": group_by},
                )
            )

        projections = ast.get("projections")
        if projections:
            stages.append(
                ExecutionStage(
                    stage_id="stage-projection",
                    operation_type="PROJECTION",
                    properties={"columns": projections},
                )
            )

        return ExecutionPlan(stages=stages)
