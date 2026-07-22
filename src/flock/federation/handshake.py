"""Secure federation handshake challenge and cluster register workflows."""

from __future__ import annotations

import time
import threading
from typing import Dict, Optional
from flock.federation.exceptions import TrustVerificationError
from flock.federation.models import TrustRelationship
from flock.security.encryption import CryptographyEngine


class FederationHandshakeManager:
    """Orchestrates secure mutual challenge-response verification for establishing federation connections."""

    def __init__(self, local_cluster_id: str, crypto: CryptographyEngine) -> None:
        self.local_cluster_id = local_cluster_id
        self._crypto = crypto
        self._lock = threading.RLock()
        self._nonces: Dict[str, str] = {}

    def generate_handshake_challenge(self, remote_cluster_id: str) -> str:
        """Generate a random cryptographic challenge nonce for mutual authentication."""
        with self._lock:
            nonce = self._crypto.generate_nonce()
            self._nonces[remote_cluster_id] = nonce
            return nonce

    def verify_handshake_response(
        self,
        remote_cluster_id: str,
        signature: str,
        certificate_pem: str,
    ) -> TrustRelationship:
        """Verify the remote cluster's signature response and issue a TrustRelationship descriptor.
        
        Raises:
            TrustVerificationError: If challenge verification or signature validation checks fail.
        """
        with self._lock:
            nonce = self._nonces.get(remote_cluster_id)
            if not nonce:
                raise TrustVerificationError("No pending challenge found for remote cluster.")
                
            payload = f"{remote_cluster_id}:{nonce}".encode("utf-8")
            try:
                self._crypto.verify_signature(payload, signature)
            except Exception as exc:
                raise TrustVerificationError(f"Handshake signature verification failed: {exc}") from exc
                
            # Clean up nonce
            del self._nonces[remote_cluster_id]
            
            now = time.time()
            # Trust relationship holds valid for 1 day
            expiry = now + 86400.0
            
            # Establish TrustRelationship signature
            trust_payload = f"{self.local_cluster_id}:{remote_cluster_id}:{expiry}".encode("utf-8")
            trust_sig = self._crypto.sign_data(trust_payload)
            
            return TrustRelationship(
                local_cluster_id=self.local_cluster_id,
                remote_cluster_id=remote_cluster_id,
                certificate_pem=certificate_pem,
                signature=trust_sig,
                established_at=now,
                valid_until=expiry,
            )
class FederationTrustStore:
    """Tracks active trust relationships and verifies peer credentials validity."""

    def __init__(self, local_cluster_id: str) -> None:
        self.local_cluster_id = local_cluster_id
        self._lock = threading.RLock()
        # remote_cluster_id -> TrustRelationship
        self._trusts: Dict[str, TrustRelationship] = {}

    def register_trust(self, trust: TrustRelationship) -> None:
        with self._lock:
            self._trusts[trust.remote_cluster_id] = trust

    def revoke_trust(self, remote_cluster_id: str) -> None:
        with self._lock:
            self._trusts.pop(remote_cluster_id, None)

    def is_trusted(self, remote_cluster_id: str) -> bool:
        """Check if remote cluster is verified and the certificate has not expired."""
        with self._lock:
            trust = self._trusts.get(remote_cluster_id)
            if not trust:
                return False
            return time.time() <= trust.valid_until
