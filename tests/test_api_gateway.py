"""Unit tests for ApiGateway."""

import time
import pytest
from flock.api.exceptions import ApiAuthenticationError, RateLimitExceededError
from flock.api.gateway import ApiGateway
from flock.api.models import ApiKey, ApiRequest


def test_gateway_authentication() -> None:
    gateway = ApiGateway()
    key = ApiKey(key_id="k-1", token="super-secret-token", expires_at=time.time() + 3600.0)
    gateway.register_key(key)

    # Missing API Key raises ApiAuthenticationError
    req_missing = ApiRequest(request_id="1", path="/data", method="GET")
    with pytest.raises(ApiAuthenticationError):
        gateway.authenticate_request(req_missing)

    # Valid API Key passes
    req_valid = ApiRequest(
        request_id="2",
        path="/data",
        method="GET",
        headers={"X-API-Key": "super-secret-token"},
    )
    gateway.authenticate_request(req_valid)


def test_gateway_rate_limiting() -> None:
    # Set limit to 2 requests/sec
    gateway = ApiGateway(rate_limit=2)

    gateway.enforce_rate_limit("127.0.0.1")
    gateway.enforce_rate_limit("127.0.0.1")

    with pytest.raises(RateLimitExceededError):
        gateway.enforce_rate_limit("127.0.0.1")
