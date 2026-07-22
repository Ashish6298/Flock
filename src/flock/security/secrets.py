"""Pluggable Secret Provider interfaces and in-memory secure storage engine."""

from __future__ import annotations

import time
import threading
from typing import Dict, Optional
from flock.security.exceptions import SecretStorageError
from flock.security.models import SecretEnvelope
from flock.security.encryption import CryptographyEngine


class VaultProvider:
    """Abstract interface for a pluggable secret provider (e.g. HashiCorp Vault, AWS Secrets Manager)."""

    def get_secret(self, secret_id: str) -> Optional[str]:
        """Retrieve the plaintext secret."""
        raise NotImplementedError

    def set_secret(self, secret_id: str, value: str) -> None:
        """Store a secret value."""
        raise NotImplementedError


class InMemoryVaultProvider(VaultProvider):
    """Simple in-memory secret provider with mock storage."""

    def __init__(self) -> None:
        self._store: Dict[str, str] = {}
        self._lock = threading.RLock()

    def get_secret(self, secret_id: str) -> Optional[str]:
        with self._lock:
            return self._store.get(secret_id)

    def set_secret(self, secret_id: str, value: str) -> None:
        with self._lock:
            self._store[secret_id] = value


class SecretsManager:
    """Manages secret envelopes, utilizing CryptographyEngine for encryption and a pluggable VaultProvider."""

    def __init__(self, crypto: CryptographyEngine, vault: Optional[VaultProvider] = None) -> None:
        self._crypto = crypto
        self._vault = vault or InMemoryVaultProvider()
        self._lock = threading.RLock()
        # Local envelopes map: secret_id -> SecretEnvelope
        self._envelopes: Dict[str, SecretEnvelope] = {}

    def store_secret(self, secret_id: str, secret_value: str) -> SecretEnvelope:
        """Encrypt secret value and save it in the vault and envelope repository."""
        with self._lock:
            # Encrypt plaintext
            ciphertext_b64, iv_hex, tag_hex = self._crypto.encrypt_aes_gcm(secret_value)
            
            envelope = SecretEnvelope(
                secret_id=secret_id,
                ciphertext=ciphertext_b64,
                iv=iv_hex,
                tag=tag_hex,
                created_at=time.time(),
                version=1,
            )
            
            # Save ciphertext envelope metadata locally
            self._envelopes[secret_id] = envelope
            # Save raw plaintext in pluggable secure vault
            self._vault.set_secret(secret_id, secret_value)
            
            return envelope

    def retrieve_secret(self, secret_id: str) -> str:
        """Retrieve and decrypt the secret using the stored envelope or secure vault provider.
        
        Raises:
            SecretStorageError: If secret cannot be located or decrypted.
        """
        with self._lock:
            # Try pluggable vault provider first
            val = self._vault.get_secret(secret_id)
            if val is not None and val != "":
                return val
                
            # If not in vault, decrypt using local envelope
            envelope = self._envelopes.get(secret_id)
            if not envelope:
                raise SecretStorageError(f"Secret '{secret_id}' not found in secret storage.")
                
            try:
                decrypted = self._crypto.decrypt_aes_gcm(
                    ciphertext_b64=envelope.ciphertext,
                    iv_hex=envelope.iv,
                    tag_hex=envelope.tag or "",
                )
                return decrypted
            except Exception as exc:
                raise SecretStorageError(f"Failed to decrypt secret envelope: {exc}") from exc

    def delete_secret(self, secret_id: str) -> None:
        """Remove a secret from all storages."""
        with self._lock:
            self._envelopes.pop(secret_id, None)
            # Remove from vault if applicable
            try:
                # Vault doesn't have an explicit delete, but we can set to empty
                self._vault.set_secret(secret_id, "")
            except Exception:
                pass
