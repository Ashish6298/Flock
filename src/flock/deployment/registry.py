"""Deployment Registry tracking revisions and rollbacks history."""

from __future__ import annotations

import threading
from typing import Dict, List, Optional

from flock.deployment.exceptions import DeploymentNotFoundError
from flock.deployment.models import DeploymentDefinition, DeploymentRevision


class DeploymentRegistry:
    """Thread-safe deployment index catalogue matching IDs to revision lists."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        
        # deployment_id -> DeploymentDefinition
        self._deployments: Dict[str, DeploymentDefinition] = {}
        # deployment_id -> list of revisions
        self._revisions: Dict[str, List[DeploymentRevision]] = {}

    def register_deployment(self, deployment: DeploymentDefinition) -> None:
        """Register deployment definition mappings."""
        with self._lock:
            self._deployments[deployment.deployment_id] = deployment
            if deployment.deployment_id not in self._revisions:
                self._revisions[deployment.deployment_id] = []

    def add_revision(self, revision: DeploymentRevision) -> None:
        """Add rollback checkpoint to revision lists."""
        with self._lock:
            revs = self._revisions.setdefault(revision.deployment_id, [])
            revs.append(revision)

    def get_deployment(self, deployment_id: str) -> Optional[DeploymentDefinition]:
        """Fetch deployment configuration."""
        with self._lock:
            return self._deployments.get(deployment_id)

    def get_revisions(self, deployment_id: str) -> List[DeploymentRevision]:
        """Fetch revisions list matching deployment target.

        Raises:
            DeploymentNotFoundError: If deployment ID is missing.
        """
        with self._lock:
            if deployment_id not in self._deployments:
                raise DeploymentNotFoundError(f"Deployment '{deployment_id}' not found.")
            return list(self._revisions.get(deployment_id, []))

    def get_latest_revision(self, deployment_id: str) -> Optional[DeploymentRevision]:
        """Fetch the latest revision for a deployment."""
        with self._lock:
            revs = self._revisions.get(deployment_id, [])
            if not revs:
                return None
            return sorted(revs, key=lambda r: r.revision_id)[-1]

    def get_previous_stable_revision(self, deployment_id: str) -> Optional[DeploymentRevision]:
        """Fetch the previous stable revision for a deployment."""
        with self._lock:
            revs = self._revisions.get(deployment_id, [])
            if len(revs) < 2:
                return None
            return sorted(revs, key=lambda r: r.revision_id)[-2]

    def prune_revisions(self, deployment_id: str, limit: int) -> int:
        """Prune obsolete revisions exceeding retention limit."""
        with self._lock:
            revs = self._revisions.get(deployment_id, [])
            if len(revs) <= limit:
                return 0
            sorted_revs = sorted(revs, key=lambda r: r.revision_id)
            pruned_count = len(sorted_revs) - limit
            self._revisions[deployment_id] = sorted_revs[-limit:]
            return pruned_count

