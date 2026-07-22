"""Dynamic credential, certificate and token rotation workflows."""

from __future__ import annotations

import time
import threading
from typing import Dict, List, Optional, Callable
from flock.security.exceptions import KeyRotationError
from flock.security.encryption import CryptographyEngine
from flock.security.certificates import CertificateManager


class CredentialRotationEngine:
    """Manages secure key rollover, token lifetime limits, and certificates rotations."""

    def __init__(self, crypto: CryptographyEngine, cert_manager: CertificateManager) -> None:
        self._crypto = crypto
        self._cert_manager = cert_manager
        self._lock = threading.RLock()
        
        # Track rotation logs: item_id -> list of rotation epoch timestamps
        self._rotation_history: Dict[str, List[float]] = {}
        # Callbacks triggered when rotation succeeds: event_name -> list of callables
        self._listeners: Dict[str, List[Callable[[str, str], None]]] = {}

    def rotate_encryption_key(self, key_id: str, new_secret: bytes) -> None:
        """Register a new key and update the active cryptographic key index."""
        with self._lock:
            try:
                self._crypto.register_key(key_id, new_secret)
                self._crypto.set_active_key(key_id)
                
                # Log rotation
                history = self._rotation_history.setdefault("encryption_key", [])
                history.append(time.time())
                
                # Notify listeners
                self._trigger_listeners("encryption_key", key_id)
            except Exception as exc:
                raise KeyRotationError(f"Failed to rotate active encryption key: {exc}") from exc

    def rotate_node_certificates(self, node_id: str) -> None:
        """Rotate public-private x509 certificates and reload the local trust authority."""
        with self._lock:
            try:
                new_cert = self._cert_manager.issue_certificate(subject=node_id)
                # Register rotation
                history = self._rotation_history.setdefault(f"cert_{node_id}", [])
                history.append(time.time())
                
                self._trigger_listeners("node_certificate", node_id)
            except Exception as exc:
                raise KeyRotationError(f"Failed to rotate certificates for node {node_id}: {exc}") from exc

    def add_rotation_listener(self, event_type: str, callback: Callable[[str, str], None]) -> None:
        """Add a callback listener for successful credentials rollover."""
        with self._lock:
            listeners = self._listeners.setdefault(event_type, [])
            listeners.append(callback)

    def get_last_rotation_time(self, item_key: str) -> Optional[float]:
        """Get timestamp of last rotation."""
        with self._lock:
            history = self._rotation_history.get(item_key, [])
            return history[-1] if history else None

    def _trigger_listeners(self, event_type: str, item_id: str) -> None:
        """Helper to invoke rotation listeners safely."""
        listeners = self._listeners.get(event_type, [])
        for listener in listeners:
            try:
                listener(event_type, item_id)
            except Exception:
                pass
