"""AES-GCM encryption, hashing, digital signatures, key rotation abstractions using only standard Python libraries or safe fallbacks."""

from __future__ import annotations

import base64
import hashlib
import hmac
import os
import time
from typing import Dict, Tuple, Optional
from flock.security.exceptions import SecurityError, SignatureVerificationError


class CryptographyEngine:
    """Helper providing hashing, HMAC signature signing, verification, and AES-GCM emulation.
    
    Uses standard libraries only (hashlib, hmac, base64) to be portable.
    Emulates AES-GCM authentication tags and IVs using HMAC-SHA256 for integrity and OS-urandom XOR-padding for privacy.
    """

    def __init__(self, secret_key: bytes) -> None:
        self._secret = secret_key
        # Active key rotation keys: key_id -> bytes
        self._rotated_keys: Dict[str, bytes] = {"v1": secret_key}
        self._active_key_id = "v1"

    def register_key(self, key_id: str, secret_key: bytes) -> None:
        """Register a key for rotation."""
        if len(secret_key) < 16:
            raise SecurityError("Secret key must be at least 16 bytes.")
        self._rotated_keys[key_id] = secret_key

    def set_active_key(self, key_id: str) -> None:
        """Set the active encryption key identifier."""
        if key_id not in self._rotated_keys:
            raise SecurityError(f"Key ID {key_id} is not registered.")
        self._active_key_id = key_id

    def generate_sha256(self, data: bytes) -> str:
        """Generate SHA-256 hex digest for a data block."""
        return hashlib.sha256(data).hexdigest()

    def generate_hmac(self, data: bytes, key_id: Optional[str] = None) -> str:
        """Generate HMAC-SHA256 signature for a data block."""
        k_id = key_id or self._active_key_id
        key = self._rotated_keys.get(k_id, self._secret)
        return hmac.new(key, data, hashlib.sha256).hexdigest()

    def verify_hmac(self, data: bytes, signature: str, key_id: Optional[str] = None) -> bool:
        """Verify if HMAC signature matches data contents securely."""
        expected = self.generate_hmac(data, key_id)
        return hmac.compare_digest(expected, signature)

    def generate_nonce(self, length: int = 16) -> str:
        """Generate a cryptographically secure random nonce string."""
        return os.urandom(length).hex()

    def encrypt_aes_gcm(self, plaintext: str, key_id: Optional[str] = None) -> Tuple[str, str, str]:
        """Encrypts data.
        
        Returns:
            Tuple of (ciphertext_b64, iv_hex, tag_hex)
        """
        k_id = key_id or self._active_key_id
        key = self._rotated_keys.get(k_id, self._secret)
        
        iv_bytes = os.urandom(12)
        iv_hex = iv_bytes.hex()
        
        # Emulate AES-GCM by deriving a unique keystream per IV using HMAC
        plain_bytes = plaintext.encode("utf-8")
        keystream_key = hmac.new(key, iv_bytes, hashlib.sha256).digest()
        
        # Simple XOR keystream generation to emulate stream cipher
        keystream = bytearray()
        while len(keystream) < len(plain_bytes):
            keystream.extend(hashlib.sha256(keystream_key + bytes([len(keystream) // 32])).digest())
        
        ciphertext_bytes = bytes(p ^ k for p, k in zip(plain_bytes, keystream))
        ciphertext_b64 = base64.b64encode(ciphertext_bytes).decode("utf-8")
        
        # Compute GCM-like Auth Tag over (IV + Ciphertext) using HMAC
        tag_hex = hmac.new(key, iv_bytes + ciphertext_bytes, hashlib.sha256).hexdigest()
        
        return ciphertext_b64, iv_hex, tag_hex

    def decrypt_aes_gcm(self, ciphertext_b64: str, iv_hex: str, tag_hex: str, key_id: Optional[str] = None) -> str:
        """Decrypts and verifies authentication of the cipher block.
        
        Raises:
            SecurityError: If authentication tag check fails.
        """
        k_id = key_id or self._active_key_id
        key = self._rotated_keys.get(k_id, self._secret)
        
        try:
            iv_bytes = bytes.fromhex(iv_hex)
            ciphertext_bytes = base64.b64decode(ciphertext_b64)
        except Exception as exc:
            raise SecurityError(f"Format decoding failed: {exc}") from exc
            
        # Verify tag before decryption (Encrypt-then-MAC paradigm)
        expected_tag = hmac.new(key, iv_bytes + ciphertext_bytes, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(expected_tag, tag_hex):
            raise SecurityError("Cryptographic integrity verification failed (Auth Tag Mismatch).")
            
        # Reconstruct keystream
        keystream_key = hmac.new(key, iv_bytes, hashlib.sha256).digest()
        keystream = bytearray()
        while len(keystream) < len(ciphertext_bytes):
            keystream.extend(hashlib.sha256(keystream_key + bytes([len(keystream) // 32])).digest())
            
        plain_bytes = bytes(c ^ k for c, k in zip(ciphertext_bytes, keystream))
        return plain_bytes.decode("utf-8")

    def sign_data(self, data: bytes) -> str:
        """Produce a digital signature over a data payload using active key."""
        return self.generate_hmac(data)

    def verify_signature(self, data: bytes, signature: str) -> None:
        """Verify signature.
        
        Raises:
            SignatureVerificationError: If verification fails.
        """
        # Try all known keys (key rotation support)
        for key_id in self._rotated_keys:
            if self.verify_hmac(data, signature, key_id):
                return
        raise SignatureVerificationError("Digital signature verification failed.")
