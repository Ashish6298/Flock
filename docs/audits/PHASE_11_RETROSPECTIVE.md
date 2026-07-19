# Phase 11 - Retrospective

## What Went Well
- **Pluggable Backoffs**: Isolating Fixed, Linear, and Exponential Jitter delay formulas within the `RetryPolicyEngine` simplified policy customizations.
- **Failover Exclusion Filters**: Modifying `PlacementEngine.place_task` to filter out specific node IDs during re-placement evaluations prevented tasks from immediately routing back to failing workers.

## Challenges & Solutions
- **Duplicate Membership in Tests**: Re-registering `server-node` on active membership registries inside test setups triggered duplicate registration errors. Adding presence checks (`if not cluster.registry.get_member("server-node")`) resolved the conflict.
- **Extended TaskStatus Enum**: Mypy caught a status verification mismatch when changing statuses to FAILED inside the scheduler registry. Extending the base `TaskStatus` enum in `src/flock/scheduler/models.py` resolved the static analysis warning.
