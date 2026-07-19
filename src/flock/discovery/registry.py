"""Catalog keeping dynamic inventory of discovered peers with automatic metadata refresh and expiration."""

import time
import structlog
from typing import Dict, Optional, List
from flock.discovery.models import NodeDescription

logger = structlog.get_logger()

class PeerRegistry:
    """catalog maintaining discovered peer node descriptions and handling metadata expiration."""

    def __init__(self, expiration_seconds: float = 30.0) -> None:
        self.expiration_seconds = expiration_seconds
        self._peers: Dict[str, NodeDescription] = {}
        self._last_seen: Dict[str, float] = {}

    def register(self, description: NodeDescription) -> bool:
        """Register or update a discovered peer.

        Returns:
            bool: True if this is a newly discovered peer, False if it was an update.
        """
        node_id = description.node_id
        is_new = node_id not in self._peers
        
        self._peers[node_id] = description
        self._last_seen[node_id] = time.time()
        
        if is_new:
            logger.info("New peer discovered and registered", node_id=node_id, host=description.host, port=description.port)
        else:
            logger.debug("Refreshed metadata for peer", node_id=node_id)
            
        return is_new

    def unregister(self, node_id: str) -> bool:
        """Remove peer from registry.

        Returns:
            bool: True if peer was registered and removed, False otherwise.
        """
        if node_id in self._peers:
            self._peers.pop(node_id)
            self._last_seen.pop(node_id, None)
            logger.info("Unregistered peer from discovery catalog", node_id=node_id)
            return True
        return False

    def get_peer(self, node_id: str) -> Optional[NodeDescription]:
        """Look up peer by identifier, checking for expiration first."""
        self.cleanup_expired()
        return self._peers.get(node_id)

    def list_peers(self) -> List[NodeDescription]:
        """List active unexpired peers."""
        self.cleanup_expired()
        return list(self._peers.values())

    def cleanup_expired(self) -> List[str]:
        """Remove nodes whose heartbeat or discovery updates have expired.

        Returns:
            List[str]: List of expired node identifiers removed.
        """
        now = time.time()
        expired_ids = []
        
        for node_id, last_update in list(self._last_seen.items()):
            if now - last_update > self.expiration_seconds:
                expired_ids.append(node_id)
                
        for node_id in expired_ids:
            self._peers.pop(node_id, None)
            self._last_seen.pop(node_id, None)
            logger.warn("Peer configuration expired", node_id=node_id)
            
        return expired_ids
