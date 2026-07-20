"""Unit tests for IdentityManager."""

import pytest
from flock.security.exceptions import AuthenticationError
from flock.security.identity import IdentityManager
from flock.security.models import NodeIdentity


def test_identity_manager_trust_registration() -> None:
    local_id = NodeIdentity(node_id="local", public_key="k1", certificate_pem="pem1")
    manager = IdentityManager(local_id)

    peer_id = NodeIdentity(node_id="peer-1", public_key="k2", certificate_pem="pem2")
    manager.register_trusted_node(peer_id)

    # Valid validation
    assert manager.verify_node_identity("peer-1", "pem2") is True

    # Check validation errors
    with pytest.raises(AuthenticationError):
        manager.verify_node_identity("peer-1", "pem-invalid")

    with pytest.raises(AuthenticationError):
        manager.verify_node_identity("unregistered-node", "pem2")
