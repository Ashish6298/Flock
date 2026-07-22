"""Platform upgrade orchestration, rollout batches, and progress updates."""

from __future__ import annotations

import threading
from typing import Dict, List, Optional
from flock.controlplane.exceptions import FleetUpgradeError
from flock.controlplane.models import FleetUpgradePlan


class UpgradeOrchestrator:
    """Manages multi-region platform rollouts and upgrades mapping."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        # upgrade_id -> FleetUpgradePlan
        self._plans: Dict[str, FleetUpgradePlan] = {}

    def schedule_upgrade(self, plan: FleetUpgradePlan) -> None:
        """Schedule a new rolling upgrade plan."""
        with self._lock:
            if plan.upgrade_id in self._plans:
                raise FleetUpgradeError(f"Upgrade plan '{plan.upgrade_id}' already registered.")
            self._plans[plan.upgrade_id] = plan

    def update_upgrade_state(self, upgrade_id: str, state: str) -> None:
        """Update overall status state of a registered upgrade rollout."""
        with self._lock:
            plan = self._plans.get(upgrade_id)
            if not plan:
                raise FleetUpgradeError(f"Upgrade plan '{upgrade_id}' not found.")
            
            self._plans[upgrade_id] = FleetUpgradePlan(
                upgrade_id=plan.upgrade_id,
                target_version=plan.target_version,
                batch_size=plan.batch_size,
                state=state,
                cluster_states=plan.cluster_states,
            )

    def set_cluster_upgrade_status(self, upgrade_id: str, cluster_id: str, state: str) -> None:
        """Set state progress of a specific cluster within the rollout plan batches."""
        with self._lock:
            plan = self._plans.get(upgrade_id)
            if not plan:
                raise FleetUpgradeError(f"Upgrade plan '{upgrade_id}' not found.")
                
            cluster_states = dict(plan.cluster_states)
            cluster_states[cluster_id] = state
            
            self._plans[upgrade_id] = FleetUpgradePlan(
                upgrade_id=plan.upgrade_id,
                target_version=plan.target_version,
                batch_size=plan.batch_size,
                state=plan.state,
                cluster_states=cluster_states,
            )

    def get_upgrade_plan(self, upgrade_id: str) -> FleetUpgradePlan:
        """Get upgrade plan details."""
        with self._lock:
            if upgrade_id not in self._plans:
                raise FleetUpgradeError(f"Upgrade plan '{upgrade_id}' not found.")
            return self._plans[upgrade_id]

    def list_upgrade_plans(self) -> List[FleetUpgradePlan]:
        """List all rollout plans."""
        with self._lock:
            return list(self._plans.values())
