"""Unit tests for AdmissionController."""

import pytest
from flock.resources.admission import AdmissionController
from flock.resources.exceptions import AdmissionFailureError
from flock.resources.models import NodeResourceProfile


def test_admission_validation() -> None:
    controller = AdmissionController(global_cpu_quota=16.0)
    node = NodeResourceProfile(node_id="n1", cpu_cores=8, cpu_util=10, memory_mb=100, memory_util=10)

    # Valid task fits
    assert controller.validate_admission({"cpu": 4.0}, node) is True

    # Denies task request exceeding node total cores
    with pytest.raises(AdmissionFailureError):
        controller.validate_admission({"cpu": 12.0}, node)

    # Denies task request exceeding global quota bounds
    with pytest.raises(AdmissionFailureError):
        controller.validate_admission({"cpu": 32.0}, node)
