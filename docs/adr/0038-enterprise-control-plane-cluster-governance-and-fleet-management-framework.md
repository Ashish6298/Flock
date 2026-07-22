# Architecture Decision Record: Phase 38 – Enterprise Control Plane, Cluster Governance & Fleet Management Framework

## Context
Governing and configuring large fleets of independent Flock clusters across multi-tenant environments requires a centralized control plane that enforces policies, manages platform rollouts, targets feature flags, schedules maintenance windows, and generates unified compliance indexes.

## Decision
We implemented a control plane subsystem under `src/flock/controlplane/` using thread-safe components and immutable Pydantic v2 data models.

Specifically:
- **`fleet.py`**: Fleet registry manager tracking organizational tenant bounds.
- **`clusters.py`**: Enrollment manager monitoring active enrolled clusters and pings.
- **`organizations.py`**: Tenant group bounds mapping.
- **`inventory.py`**: Search indices mapping cluster labels for inventory queries.
- **`governance.py`**: Evaluates policy rules (like min_version limits) and compliance.
- **`policies.py`**: GovernancePolicyManager compatibility alias.
- **`configuration.py`**: Version-controlled override configuration values database.
- **`featureflags.py`**: Targets flag activations globally or to specific cluster targets.
- **`maintenance.py`**: Window scheduling with overlap detection rules.
- **`upgrades.py`**: Multi-region rolling upgrades orchestrator.
- **`compliance.py`**: Runs evaluation audits and computes compliance scores.
- **`analytics.py`**: Tracks active count metrics.
- **`audit.py`**: Records control plane enrollment events.
- **`coordinator.py`**: Entrypoint wrapping fleet control engines.
- **`service.py`**: Maps MessageBus endpoints (`CLUSTER_ENROLLMENT` and `GOVERNANCE_SYNC`) and fires EventBus events.

## Consequences
- **Fleet Control**: Administrators can dynamically manage rollouts and features globally.
- **Mypy Strict Compliance**: Achieved 0 warnings or errors.
- **Verification**: All 610 regression tests pass cleanly.
