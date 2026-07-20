"""Identity Manager handling node public keys and certificate validations."""

from __future__ import annotations

from typing import Dict, Optional

from flock.security.exceptions import AuthenticationError
from flock.security.models import NodeIdentity


class IdentityManager:
    """Manages local node credentials and keeps validation catalogs for peers."""

    def __init__(self, local_identity: NodeIdentity) -> None:
        self.local_identity = local_identity
        # Catalog of trusted node identities: node_id -> NodeIdentity
        self._trusted_nodes: Dict[str, NodeIdentity] = {}

    def register_trusted_node(self, identity: NodeIdentity) -> None:
        """Register a peer node's certificate in the trust store catalog."""
        self._trusted_nodes[identity.node_id] = identity

    def verify_node_identity(self, node_id: str, certificate_pem: str) -> bool:
        """Verify node's identity against the catalog.

        Raises:
            AuthenticationError: If identity doesn't match or is missing.
        """
        if node_id not in self._trusted_nodes:
            raise AuthenticationError(f"Node '{node_id}' is not trusted (missing registration).")
        
        expected = self._trusted_nodes[node_id]
        if expected.certificate_pem != certificate_pem:
            raise AuthenticationError(f"Certificate mismatch for node '{node_id}'.")

        return True
