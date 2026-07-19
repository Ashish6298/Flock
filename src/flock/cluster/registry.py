"""Authoritative catalog containing in-memory cluster view mapping details."""

import structlog
from typing import Dict, List, Optional
from flock.cluster.models import ClusterMember, ClusterMemberStatus
from flock.cluster.exceptions import MembershipStateError, DuplicateMembershipError

logger = structlog.get_logger()

class MembershipRegistry:
    """Asyncio-safe membership registry container tracking cluster membership entries and metadata versions."""

    def __init__(self) -> None:
        self._members: Dict[str, ClusterMember] = {}
        self.version = 0

    def add_member(self, member: ClusterMember) -> None:
        """Add new member to cluster registry.

        Raises:
            DuplicateMembershipError: If node ID already registered.
        """
        node_id = member.node_id
        if node_id in self._members:
            raise DuplicateMembershipError(f"Node identifier already registered: {node_id}")
        
        self._members[node_id] = member
        self.version += 1
        logger.info("Added node to cluster registry", node_id=node_id, version=self.version)

    def update_status(self, node_id: str, new_status: ClusterMemberStatus) -> None:
        """Deterministic lifecycle state transitions.

        Raises:
            MembershipStateError: If transition is illegal.
        """
        member = self._members.get(node_id)
        if not member:
            raise MembershipStateError(f"Node identifier {node_id} is not registered in cluster")

        current = member.status
        # Transition check rules
        if current == ClusterMemberStatus.REMOVED:
            raise MembershipStateError(f"Cannot transition node {node_id} from REMOVED state")
        if current == ClusterMemberStatus.REJECTED:
            raise MembershipStateError(f"Cannot transition node {node_id} from REJECTED state")
        
        # Valid update
        updated = ClusterMember(
            node_id=member.node_id,
            description=member.description,
            status=new_status,
            join_timestamp=member.join_timestamp,
            membership_version=member.membership_version + 1,
            role=member.role
        )
        self._members[node_id] = updated
        self.version += 1
        logger.info("Updated node status in cluster registry", node_id=node_id, from_status=current, to_status=new_status, version=self.version)

    def remove_member(self, node_id: str) -> None:
        """Remove member from catalog or transition status to REMOVED."""
        if node_id in self._members:
            self.update_status(node_id, ClusterMemberStatus.REMOVED)
            self._members.pop(node_id, None)
            self.version += 1
            logger.info("Removed node from active cluster list", node_id=node_id, version=self.version)

    def get_member(self, node_id: str) -> Optional[ClusterMember]:
        """Look up member details by ID."""
        return self._members.get(node_id)

    def list_members(self, status: Optional[ClusterMemberStatus] = None) -> List[ClusterMember]:
        """List active members matching filters."""
        if status:
            return [m for m in self._members.values() if m.status == status]
        return list(self._members.values())
