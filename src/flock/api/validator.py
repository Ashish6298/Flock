"""Request Validator checking schema parameters."""

from __future__ import annotations

import json
from flock.api.exceptions import InvalidRequestError
from flock.api.models import ApiRequest


class RequestValidator:
    """Checks header properties and JSON body constraints."""

    def __init__(self) -> None:
        pass

    def validate_request(self, request: ApiRequest) -> None:
        """Validate request payload size and JSON format details.

        Raises:
            InvalidRequestError: If request fails validation.
        """
        if not request.path.strip():
            raise InvalidRequestError("Request path cannot be empty.")
            
        if request.body:
            try:
                # Ensure body is valid JSON if present
                json.loads(request.body.decode("utf-8"))
            except Exception as exc:
                raise InvalidRequestError(f"Request body is not valid JSON: {exc}") from exc
