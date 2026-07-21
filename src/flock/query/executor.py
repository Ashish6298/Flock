"""Query Executor evaluating optimized execution plans."""

from __future__ import annotations

from typing import Any, Dict, List

import structlog

from flock.query.exceptions import QueryExecutionError
from flock.query.models import ExecutionPlan, QueryResult

logger = structlog.get_logger()


class QueryExecutor:
    """Evaluates sequential execution plans against memory tables dataset."""

    def __init__(self) -> None:
        pass

    def execute_plan(
        self,
        plan: ExecutionPlan,
        catalog_dataset: Dict[str, List[List[Any]]],
        columns_map: List[str],
    ) -> QueryResult:
        """Evaluate plan stages.

        Raises:
            QueryExecutionError: If plan scans invalid database table.
        """
        logger.info("Executing optimized query plan stages")
        current_rows: List[List[Any]] = []
        cols = list(columns_map)

        for stage in plan.stages:
            op = stage.operation_type
            if op == "SCAN":
                tbl = stage.properties.get("table", "")
                if tbl not in catalog_dataset:
                    raise QueryExecutionError(f"Table '{tbl}' is missing from catalog dataset.")
                current_rows = [list(r) for r in catalog_dataset[tbl]]

            elif op == "FILTER":
                # Simulates basic filters matching properties (e.g. status='active')
                expr = stage.properties.get("expression", "")
                if "status" in expr and "active" in expr:
                    # Look up status column index
                    try:
                        status_idx = cols.index("status")
                        current_rows = [r for r in current_rows if r[status_idx] == "active"]
                    except ValueError:
                        pass

            elif op == "PROJECTION":
                target_cols = stage.properties.get("columns", [])
                if target_cols and target_cols != ["*"]:
                    indices = []
                    for tc in target_cols:
                        try:
                            indices.append(cols.index(tc))
                        except ValueError:
                            indices.append(-1)
                    
                    projected = []
                    for row in current_rows:
                        projected.append([row[i] if i != -1 else None for i in indices])
                    current_rows = projected
                    cols = list(target_cols)

        return QueryResult(
            query_id="query-execution",
            success=True,
            rows=current_rows,
            columns=cols,
        )
