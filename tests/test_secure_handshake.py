"""Unit tests for SecureHandshakeManager."""

import pytest
from flock.security.crypto import CryptographyEngine
from flock.security.exceptions import AuthenticationError
from flock.security.handshake import SecureHandshakeManager
from flock.security.identity import IdentityManager
from flock.security.models import NodeIdentity


def test_mutual_handshake_challenge() -> None:
    crypto = CryptographyEngine(b"secret")
    local_id = NodeIdentity(node_id="local", public_key="k1", certificate_pem="pem1")
    identity = IdentityManager(local_id)
    
    peer_id = NodeIdentity(node_id="peer-1", public_key="k2", certificate_pem="pem2")
    identity.register_trusted_node(peer_id)

    handshake = SecureHandshakeManager(crypto, identity)

    # 1. Challenge generation
    nonce = handshake.generate_challenge("peer-1")
    assert nonce is not None

    # 2. Challenge response signing
    sig = crypto.generate_hmac(nonce.encode("utf-8"))

    # 3. Verify
    assert handshake.verify_response("peer-1", sig, "pem2") is True


def test_handshake_corrupted_response_raises() -> None:
    crypto = CryptographyEngine(b"secret")
    local_id = NodeIdentity(node_id="local", public_key="k1", certificate_pem="pem1")
    identity = IdentityManager(local_id)
    
    peer_id = NodeIdentity(node_id="peer-1", public_key="k2", certificate_pem="pem2")
    identity.register_trusted_node(peer_id)

    handshake = SecureHandshakeManager(crypto, identity)
    nonce = handshake.generate_challenge("peer-1")

    # Invalid signature response
    with pytest.raises(AuthenticationError):
        handshake.verify_response("peer-1", "invalid-sig", "pem2")
