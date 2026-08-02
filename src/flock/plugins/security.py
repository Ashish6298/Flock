"""Plugin Security Manager.

Evaluates permissions, enforces capability mappings, registers policies,
and records audit logs with a fail-safe default-deny pattern.
"""

from __future__ import annotations

import fnmatch
import threading
import uuid
from typing import Dict

import structlog

from flock.plugins.exceptions import PluginPermissionDeniedError
from flock.plugins.models import (
    PermissionDecision,
    PermissionRequest,
    PermissionScope,
    PluginAuditEntry,
    PluginPermission,
    SecurityPolicy,
    SecurityViolation,
)
from flock.plugins.registry import PluginRegistry

logger = structlog.get_logger()


class PluginSecurityManager:
    """Thread-safe policy engine assessing resource permissions using default-deny rules."""

    def __init__(self, registry: PluginRegistry) -> None:
        self._registry = registry
        self._lock = threading.RLock()
        self._decision_cache: Dict[str, PermissionDecision] = {}

    def register_policy(self, policy: SecurityPolicy) -> None:
        """Saves a security policy definition in the registry."""
        self._registry.register_security_policy(policy)
        self.clear_decision_cache()

    def grant_explicit_permission(self, perm: PluginPermission) -> None:
        """Saves an explicit permission grant."""
        self._registry.grant_permission(perm)
        self.clear_decision_cache()

    def clear_decision_cache(self) -> None:
        """Invalidates all cached evaluation decisions."""
        with self._lock:
            self._decision_cache.clear()

    def check_permission(self, plugin_id: str, scope: PermissionScope, resource: str) -> bool:
        """Determines if a plugin is allowed to access a resource scope. Default-deny model."""
        cache_key = f"{plugin_id}:{scope.value}:{resource}"
        
        with self._lock:
            if cache_key in self._decision_cache:
                return self._decision_cache[cache_key].allowed

        allowed = self._evaluate_permission_decision(plugin_id, scope, resource)
        
        decision = PermissionDecision(
            decision_id=str(uuid.uuid4()),
            plugin_id=plugin_id,
            scope=scope,
            resource=resource,
            allowed=allowed,
        )

        with self._lock:
            self._decision_cache[cache_key] = decision

        # Record audit log entry
        self._log_audit_and_violation(plugin_id, scope, resource, allowed)
        return allowed

    def verify_permission(self, plugin_id: str, scope: PermissionScope, resource: str) -> None:
        """Asserts permission, raising PluginPermissionDeniedError on failure."""
        if not self.check_permission(plugin_id, scope, resource):
            raise PluginPermissionDeniedError(
                f"Permission denied: Plugin '{plugin_id}' lacks '{scope.value}' access on '{resource}'."
            )

    def request_permission(self, req: PermissionRequest) -> bool:
        """Allows a plugin to request a permission at runtime. Resolves based on rules."""
        # Simple auto-grant logic based on policy match or default deny
        is_granted = self.check_permission(req.plugin_id, req.scope, req.resource)
        if is_granted:
            perm = PluginPermission(
                permission_id=str(uuid.uuid4()),
                plugin_id=req.plugin_id,
                scope=req.scope,
                resource=req.resource,
                is_granted=True,
            )
            self.grant_explicit_permission(perm)
        return is_granted

    def _evaluate_permission_decision(self, plugin_id: str, scope: PermissionScope, resource: str) -> bool:
        """Assesses policies and explicit permission grants in a deterministic order."""
        # 1. Deny check (Policies)
        policies = self._registry.get_security_policies()
        
        # Sort policies deterministically by ID to ensure consistency
        policies.sort(key=lambda p: p.policy_id)

        # Check explicit denies first
        for policy in policies:
            if fnmatch.fnmatch(plugin_id, policy.plugin_id_pattern):
                if scope in policy.denied_permissions:
                    return False

        # 2. Check explicit permission grants
        granted = self._registry.query_permissions(plugin_id)
        for perm in granted:
            if perm.scope == scope and (perm.resource == "*" or fnmatch.fnmatch(resource, perm.resource)):
                if perm.is_granted:
                    return True

        # 3. Check policy allows
        for policy in policies:
            if fnmatch.fnmatch(plugin_id, policy.plugin_id_pattern):
                if scope in policy.allowed_permissions:
                    return True

        # Default Deny
        return False

    def _log_audit_and_violation(self, plugin_id: str, scope: PermissionScope, resource: str, allowed: bool) -> None:
        """Appends audit entries and policy violations based on decision status."""
        entry_id = str(uuid.uuid4())
        status = "SUCCESS" if allowed else "DENIED"
        details = f"Scope: '{scope.value}', Resource: '{resource}'"

        audit_entry = PluginAuditEntry(
            entry_id=entry_id,
            plugin_id=plugin_id,
            action="CHECK_PERMISSION",
            status=status,
            details=details,
        )
        self._registry.record_audit_entry(audit_entry)

        if not allowed:
            violation_id = str(uuid.uuid4())
            violation = SecurityViolation(
                violation_id=violation_id,
                plugin_id=plugin_id,
                attempted_action="CHECK_PERMISSION",
                required_scope=scope,
                details=f"Unauthorized access to scope '{scope.value}' on resource '{resource}'",
            )
            self._registry.record_security_violation(violation)
