"""Unit tests for CryptographyEngine."""

from flock.security.crypto import CryptographyEngine


def test_crypto_hashing_and_hmac() -> None:
    secret = b"cluster-secret-key-12345"
    engine = CryptographyEngine(secret)

    # SHA256 hashing
    h1 = engine.generate_sha256(b"hello")
    h2 = engine.generate_sha256(b"hello")
    assert h1 == h2

    # HMAC signing & validation
    sig = engine.generate_hmac(b"payload-bytes")
    assert engine.verify_hmac(b"payload-bytes", sig) is True
    assert engine.verify_hmac(b"payload-bytes-corrupt", sig) is False
