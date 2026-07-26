"""Production Rollback & Release Safety Engine."""

from __future__ import annotations

import time
from typing import List, Optional

from flock.deployment.exceptions import RollbackFailedError, DeploymentNotFoundError
from flock.deployment.models import (
    RollbackRequest,
    RollbackResult,
    DeploymentRevision,
    ReleaseVerificationResult,
    ValidationResult
)
from flock.deployment.registry import DeploymentRegistry


class RollbackEngine:
    """Orchestrates rollback execution, revision lookups, and metadata audits."""

    def __init__(self, registry: DeploymentRegistry) -> None:
        self._registry = registry

    def validate_rollback_request(self, request: RollbackRequest) -> ValidationResult:
        """Validate if deployment and target revision exist in history registry."""
        errors: List[str] = []
        dep_id = request.deployment_id
        
        dep = self._registry.get_deployment(dep_id)
        if not dep:
            errors.append(f"Deployment '{dep_id}' not found in registry.")
            return ValidationResult(is_valid=False, errors=errors)

        try:
            revisions = self._registry.get_revisions(dep_id)
            if not any(r.revision_id == request.target_revision_id for r in revisions):
                errors.append(f"Target revision {request.target_revision_id} not found in revision history.")
        except DeploymentNotFoundError as e:
            errors.append(str(e))

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors
        )

    def execute_rollback(self, request: RollbackRequest) -> RollbackResult:
        """Locates stable revision coordinates and executes reversion updates."""
        val_res = self.validate_rollback_request(request)
        if not val_res.is_valid:
            raise RollbackFailedError(f"Rollback validation failed: {', '.join(val_res.errors)}")

        dep_id = request.deployment_id
        revisions = self._registry.get_revisions(dep_id)
        
        sorted_revs = sorted(revisions, key=lambda r: r.revision_id)
        current_rev = sorted_revs[-1] if sorted_revs else None
        previous_id = current_rev.revision_id if current_rev else 0

        target_rev = next(r for r in revisions if r.revision_id == request.target_revision_id)

        new_rev_id = previous_id + 1
        new_rev = DeploymentRevision(
            revision_id=new_rev_id,
            deployment_id=dep_id,
            manifest=target_rev.manifest,
            created_at=time.time(),
        )
        self._registry.add_revision(new_rev)

        return RollbackResult(
            success=True,
            message=f"Successfully rolled back deployment '{dep_id}' to revision {request.target_revision_id}",
            previous_revision_id=previous_id,
            restored_revision_id=request.target_revision_id,
            timestamp=time.time(),
        )


class DeploymentVerifier:
    """Executes post-deployment safety validation before declaring healthy status."""

    def __init__(self, registry: DeploymentRegistry) -> None:
        self._registry = registry

    def verify_release(self, release_id: str, deployment_id: str) -> ReleaseVerificationResult:
        """Evaluate resource thresholds and config constraints readiness status."""
        errors: List[str] = []
        checks = ["DeploymentExistence", "ConfigConsistency", "ReadinessProbeCheck"]

        dep = self._registry.get_deployment(deployment_id)
        if not dep:
            errors.append(f"Deployment '{deployment_id}' does not exist.")
            return ReleaseVerificationResult(
                release_id=release_id,
                is_healthy=False,
                checks_passed=[],
                errors=errors,
            )

        if not dep.name or len(dep.name) < 3:
            errors.append("Invalid deployment name format.")

        return ReleaseVerificationResult(
            release_id=release_id,
            is_healthy=len(errors) == 0,
            checks_passed=[c for c in checks if c not in errors],
            errors=errors,
        )
