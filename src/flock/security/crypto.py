"""Cryptography Engine supporting HMAC signing and SHA-256 validation."""

from __future__ import annotations

import hmac
import hashlib
import os
from typing import Tuple


class CryptographyEngine:
    """Helper providing hashing, HMAC signature signing, and verification."""

    def __init__(self, secret_key: bytes) -> None:
        self._secret = secret_key

    def generate_sha256(self, data: bytes) -> str:
        """Generate SHA-256 hex digest for a data block."""
        return hashlib.sha256(data).hexdigest()

    def generate_hmac(self, data: bytes) -> str:
        """Generate HMAC-SHA256 signature for a data block."""
        return hmac.new(self._secret, data, hashlib.sha256).hexdigest()

    def verify_hmac(self, data: bytes, signature: str) -> bool:
        """Verify if HMAC signature matches data contents securely."""
        expected = self.generate_hmac(data)
        return hmac.compare_digest(expected, signature)

    def generate_nonce(self) -> str:
        """Generate a cryptographically secure random nonce string."""
        return os.urandom(16).hex()
