"""Unit tests for RequestValidator."""

import pytest
from flock.api.exceptions import InvalidRequestError
from flock.api.models import ApiRequest
from flock.api.validator import RequestValidator


def test_validator_enforces_path_and_json() -> None:
    validator = RequestValidator()

    # Empty path raises error
    req_empty = ApiRequest(request_id="1", path="", method="GET")
    with pytest.raises(InvalidRequestError):
        validator.validate_request(req_empty)

    # Invalid JSON body raises error
    req_invalid_json = ApiRequest(request_id="2", path="/jobs", method="POST", body=b"invalid-json")
    with pytest.raises(InvalidRequestError):
        validator.validate_request(req_invalid_json)

    # Valid JSON fits
    req_valid = ApiRequest(request_id="3", path="/jobs", method="POST", body=b'{"id": 42}')
    validator.validate_request(req_valid)
