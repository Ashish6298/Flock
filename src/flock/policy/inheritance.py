"""Policy inheritance resolver (combining parent and child policies rules)."""

from __future__ import annotations

import threading
from typing import Dict, List, Optional
from flock.policy.models import PolicyDefinition
from flock.policy.repository import PolicyRepository


class PolicyInheritanceResolver:
    """Resolves hierarchical policy inheritances, combining parent rule lists with child rules."""

    def __init__(self, repository: PolicyRepository) -> None:
        self._repo = repository

    def resolve_effective_rules(self, policy: PolicyDefinition) -> PolicyDefinition:
        """Trace parent policy hierarchy and return a compiled policy containing combined rules."""
        effective_rules = list(policy.rules)
        current = policy
        
        # Traverse parent chain
        visited = {policy.policy_id}
        while current.parent_policy_id:
            parent_id = current.parent_policy_id
            if parent_id in visited:
                break  # Prevent infinite cycle loops
            visited.add(parent_id)
            
            try:
                parent = self._repo.get_policy(parent_id)
                effective_rules.extend(parent.rules)
                current = parent
            except Exception:
                # Parent missing in repository; stop trace
                break
                
        return PolicyDefinition(
            policy_id=policy.policy_id,
            version=policy.version,
            target_selectors=policy.target_selectors,
            rules=effective_rules,
            parent_policy_id=policy.parent_policy_id,
        )
