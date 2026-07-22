"""API keys, credentials, token authentication mechanisms."""

from __future__ import annotations

import time
from typing import Dict, Optional, Set
from flock.security.exceptions import AuthenticationError
from flock.security.models import SessionToken
from flock.security.encryption import CryptographyEngine


class AuthenticationEngine:
    """Authenticates API keys and checks signature tokens."""

    def __init__(self, crypto: CryptographyEngine) -> None:
        self._crypto = crypto
        # api_key -> client_name
        self._api_keys: Dict[str, str] = {}
        # Revoked tokens set
        self._revoked_tokens: Set[str] = set()

    def register_api_key(self, api_key: str, client_name: str) -> None:
        """Register a client API key."""
        self._api_keys[api_key] = client_name

    def revoke_api_key(self, api_key: str) -> None:
        """Revoke a client API key."""
        self._api_keys.pop(api_key, None)

    def authenticate_api_key(self, api_key: str) -> str:
        """Authenticate API key and return the associated client name.
        
        Raises:
            AuthenticationError: If the API key is not registered.
        """
        if api_key not in self._api_keys:
            raise AuthenticationError("Invalid or missing API key.")
        return self._api_keys[api_key]

    def verify_session_token(self, token: SessionToken) -> bool:
        """Verify the integrity, signature, and expiration of a session token.
        
        Raises:
            AuthenticationError: If the token is invalid or expired.
        """
        if token.token_id in self._revoked_tokens:
            raise AuthenticationError("Session token has been revoked.")
            
        if time.time() > token.expires_at:
            raise AuthenticationError("Session token has expired.")
            
        # Re-verify token signature payload: token_id:subject:expires_at
        payload = f"{token.token_id}:{token.subject}:{token.expires_at}".encode("utf-8")
        if not self._crypto.verify_hmac(payload, token.signature):
            raise AuthenticationError("Session token signature verification failed.")
            
        return True

    def revoke_session_token(self, token_id: str) -> None:
        """Revoke a session token by ID."""
        self._revoked_tokens.add(token_id)
