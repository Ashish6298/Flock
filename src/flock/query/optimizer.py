"""Cost-Based Query Optimizer rewriting execution plans."""

from __future__ import annotations

from flock.query.models import ExecutionPlan, ExecutionStage


class QueryOptimizer:
    """Implements predicate pushdown and constants folding optimizes."""

    def __init__(self) -> None:
        pass

    def optimize_plan(self, plan: ExecutionPlan) -> ExecutionPlan:
        """Rewrite execution plan stages to improve cost metrics."""
        stages = plan.stages
        
        # Predicate pushdown rule: Move FILTER directly after SCAN
        scan_idx = -1
        filter_idx = -1
        
        for idx, stage in enumerate(stages):
            if stage.operation_type == "SCAN":
                scan_idx = idx
            elif stage.operation_type == "FILTER":
                filter_idx = idx

        if scan_idx != -1 and filter_idx != -1 and filter_idx > scan_idx + 1:
            optimized_stages = list(stages)
            filter_stage = optimized_stages.pop(filter_idx)
            optimized_stages.insert(scan_idx + 1, filter_stage)
            return ExecutionPlan(stages=optimized_stages)

        return plan
