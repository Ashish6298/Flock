"""Token Manager issuing and verifying HMAC-signed tokens."""

from __future__ import annotations

import time
import uuid
from typing import Dict, Optional

from flock.security.crypto import CryptographyEngine
from flock.security.exceptions import TokenExpiredError, SignatureVerificationError
from flock.security.models import SessionToken


class TokenManager:
    """Creates, signs, and validates SessionTokens using CryptographyEngine."""

    def __init__(self, crypto: CryptographyEngine, default_ttl_seconds: int = 3600) -> None:
        self._crypto = crypto
        self.default_ttl = default_ttl_seconds
        self._revocation_list: Dict[str, float] = {}

    def issue_token(self, subject: str) -> SessionToken:
        """Create and sign a new SessionToken for a subject."""
        tid = str(uuid.uuid4())
        expires = time.time() + self.default_ttl

        # Signature binds subject, id, and expiry timestamp
        sign_payload = f"{tid}:{subject}:{expires}".encode("utf-8")
        signature = self._crypto.generate_hmac(sign_payload)

        return SessionToken(
            token_id=tid,
            subject=subject,
            expires_at=expires,
            signature=signature,
        )

    def validate_token(self, token: SessionToken) -> bool:
        """Verify session token signature and expiration limits.

        Raises:
            SignatureVerificationError: If HMAC hash mismatch occurs.
            TokenExpiredError: If token deadline is passed or revoked.
        """
        # 1. Check revocation
        if token.token_id in self._revocation_list:
            raise TokenExpiredError("Token has been explicitly revoked.")

        # 2. Check expiration
        if time.time() > token.expires_at:
            raise TokenExpiredError("Token validity deadline expired.")

        # 3. Verify Signature
        sign_payload = f"{token.token_id}:{token.subject}:{token.expires_at}".encode("utf-8")
        if not self._crypto.verify_hmac(sign_payload, token.signature):
            raise SignatureVerificationError("HMAC verification failed for session token.")

        return True

    def revoke_token(self, token_id: str) -> None:
        """Add token to revocation list."""
        self._revocation_list[token_id] = time.time()
