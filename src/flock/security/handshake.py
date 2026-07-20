"""Secure Handshake Manager for node validation on cluster join."""

from __future__ import annotations

import time
from typing import Dict

from flock.security.crypto import CryptographyEngine
from flock.security.exceptions import AuthenticationError
from flock.security.identity import IdentityManager


class SecureHandshakeManager:
    """Orchestrates node identity challenges to verify joining credentials."""

    def __init__(self, crypto: CryptographyEngine, identity: IdentityManager) -> None:
        self._crypto = crypto
        self._identity = identity
        
        # Outstanding challenges: node_id -> expected response payload (e.g. signed nonce)
        # For challenge response: we store node_id -> sent nonce
        self._challenges: Dict[str, str] = {}

    def generate_challenge(self, node_id: str) -> str:
        """Create random challenge nonce for node verification."""
        nonce = self._crypto.generate_nonce()
        self._challenges[node_id] = nonce
        return nonce

    def verify_response(self, node_id: str, signature: str, certificate_pem: str) -> bool:
        """Verify the challenge response from the joining node.

        Raises:
            AuthenticationError: If nonce signature is invalid or mismatched.
        """
        # Validate node certificate exists in trusted catalog
        self._identity.verify_node_identity(node_id, certificate_pem)

        expected_nonce = self._challenges.pop(node_id, None)
        if not expected_nonce:
            raise AuthenticationError(f"No active challenge session found for node '{node_id}'.")

        # Verify signature using shared secret HMAC (acting as challenge signature verifier)
        payload = expected_nonce.encode("utf-8")
        if not self._crypto.verify_hmac(payload, signature):
            raise AuthenticationError("Challenge-response signature verification failed.")

        return True
