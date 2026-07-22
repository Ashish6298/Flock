"""Tenant organization management, hierarchical resource boundaries, and memberships."""

from __future__ import annotations

import threading
from typing import Dict, List, Set


class OrganizationManager:
    """Manages multi-tenant organization boundaries and resource groups mapping."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        # org_id -> set of tenant member ids
        self._org_members: Dict[str, Set[str]] = {}

    def create_organization(self, org_id: str) -> None:
        """Register a new organization tenant scope."""
        with self._lock:
            if org_id not in self._org_members:
                self._org_members[org_id] = set()

    def add_tenant_member(self, org_id: str, member_id: str) -> None:
        """Assign member identification tag under tenant org namespace."""
        with self._lock:
            self.create_organization(org_id)
            self._org_members[org_id].add(member_id)

    def is_member(self, org_id: str, member_id: str) -> bool:
        """Verify membership relation matches under organization bounds."""
        with self._lock:
            return member_id in self._org_members.get(org_id, set())

    def list_orgs(self) -> List[str]:
        """List all active organization identifiers."""
        with self._lock:
            return list(self._org_members.keys())
