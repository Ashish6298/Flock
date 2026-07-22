"""Automated node isolation, peer quarantines, and administrative recoveries."""

from __future__ import annotations

import time
import threading
from typing import Dict, List, Optional
from flock.security.exceptions import QuarantineError
from flock.security.models import QuarantineStatus


class QuarantineManager:
    """Isolates malicious or degraded cluster nodes based on security breaches."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        # node_id -> QuarantineStatus
        self._quarantines: Dict[str, QuarantineStatus] = {}

    def quarantine_node(
        self,
        node_id: str,
        reason: str,
        duration_seconds: Optional[float] = None,
    ) -> QuarantineStatus:
        """Isolate a node from cluster operations."""
        with self._lock:
            now = time.time()
            until = (now + duration_seconds) if duration_seconds else None
            
            status = QuarantineStatus(
                node_id=node_id,
                isolated=True,
                reason=reason,
                isolated_at=now,
                quarantine_until=until,
            )
            self._quarantines[node_id] = status
            return status

    def recover_node(self, node_id: str) -> QuarantineStatus:
        """Reinstate a node back into trusted service operations."""
        with self._lock:
            if node_id not in self._quarantines:
                raise QuarantineError(f"Node '{node_id}' is not in quarantine registry.")
                
            status = QuarantineStatus(
                node_id=node_id,
                isolated=False,
                reason="Administrative recovery completed.",
                isolated_at=None,
                quarantine_until=None,
            )
            self._quarantines[node_id] = status
            return status

    def is_isolated(self, node_id: str) -> bool:
        """Check if a node is currently under isolation.
        
        Handles automatic TTL expiration of quarantine durations.
        """
        with self._lock:
            if node_id not in self._quarantines:
                return False
            status = self._quarantines[node_id]
            if not status.isolated:
                return False
            
            # Check expiration TTL
            if status.quarantine_until and time.time() > status.quarantine_until:
                # Expired -> Recover automatically
                self._quarantines[node_id] = QuarantineStatus(
                    node_id=node_id,
                    isolated=False,
                    reason="Quarantine duration expired.",
                    isolated_at=None,
                    quarantine_until=None,
                )
                return False
                
            return True

    def get_quarantine_status(self, node_id: str) -> QuarantineStatus:
        """Get the current quarantine parameters for a node."""
        with self._lock:
            if node_id not in self._quarantines:
                return QuarantineStatus(node_id=node_id, isolated=False, reason="Node is active and trusted.")
            # Trigger expiration check to ensure accurate status
            self.is_isolated(node_id)
            return self._quarantines[node_id]

    def list_isolated_nodes(self) -> List[str]:
        """List all isolated node IDs."""
        with self._lock:
            # Trigger checks to clear expired quarantine TTLs
            return [nid for nid in self._quarantines if self.is_isolated(nid)]
