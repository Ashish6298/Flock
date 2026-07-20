"""Unit tests for TokenManager."""

import pytest
import time
from flock.security.crypto import CryptographyEngine
from flock.security.exceptions import TokenExpiredError
from flock.security.token import TokenManager


def test_token_creation_and_expiration() -> None:
    crypto = CryptographyEngine(b"secret")
    # Short TTL to test validation expiration checks
    manager = TokenManager(crypto, default_ttl_seconds=-10)

    token = manager.issue_token("node-1")
    assert token.subject == "node-1"

    with pytest.raises(TokenExpiredError):
        manager.validate_token(token)


def test_token_revocation() -> None:
    crypto = CryptographyEngine(b"secret")
    manager = TokenManager(crypto, default_ttl_seconds=100)

    token = manager.issue_token("node-1")
    assert manager.validate_token(token) is True

    # Revoke
    manager.revoke_token(token.token_id)
    with pytest.raises(TokenExpiredError):
        manager.validate_token(token)
