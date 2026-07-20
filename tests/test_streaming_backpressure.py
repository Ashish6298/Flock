"""Unit tests for BackpressureController."""

import pytest
from flock.streaming.backpressure import BackpressureController
from flock.streaming.exceptions import BackpressureLimitExceededError


def test_backpressure_enforcement() -> None:
    # Set limit to 2 messages per window
    controller = BackpressureController(max_rate=2, window_seconds=1.0)

    controller.record_and_assert()
    controller.record_and_assert()

    # 3rd message triggers backpressure violation error
    with pytest.raises(BackpressureLimitExceededError):
        controller.record_and_assert()
