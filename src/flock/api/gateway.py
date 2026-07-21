"""API Gateway managing keys, tokens, and rate limits."""

from __future__ import annotations

import time
from typing import Dict, Set

from flock.api.exceptions import ApiAuthenticationError, RateLimitExceededError
from flock.api.models import ApiKey, ApiRequest


class ApiGateway:
    """Enforces rate limits and validates client API keys."""

    def __init__(self, rate_limit: int = 100) -> None:
        self.rate_limit = rate_limit
        
        # key_id -> ApiKey
        self._keys: Dict[str, ApiKey] = {}
        # ip_address -> list of timestamps
        self._rate_limits: Dict[str, list[float]] = {}

    def register_key(self, api_key: ApiKey) -> None:
        """Register client api key metadata."""
        self._keys[api_key.key_id] = api_key

    def authenticate_request(self, request: ApiRequest) -> None:
        """Verify API key credentials.

        Raises:
            ApiAuthenticationError: If API key is missing or expired.
        """
        token = request.headers.get("X-API-Key")
        if not token:
            raise ApiAuthenticationError("Missing API Key header 'X-API-Key'.")

        # Find token match
        match = None
        for key in self._keys.values():
            if key.token == token:
                match = key
                break

        if not match:
            raise ApiAuthenticationError("Invalid API Key.")

        if time.time() > match.expires_at:
            raise ApiAuthenticationError("API Key has expired.")

    def enforce_rate_limit(self, client_ip: str) -> None:
        """Verify request frequency.

        Raises:
            RateLimitExceededError: If client IP exceeds throttling window limits.
        """
        now = time.time()
        stamps = self._rate_limits.setdefault(client_ip, [])
        
        # Keep window to last 1 second
        stamps = [t for t in stamps if now - t < 1.0]
        self._rate_limits[client_ip] = stamps

        if len(stamps) >= self.rate_limit:
            raise RateLimitExceededError("Rate limit exceeded. Please slow down.")

        stamps.append(now)
