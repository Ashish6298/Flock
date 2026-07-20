"""Admission Controller verifying task constraints and quotas."""

from __future__ import annotations

from typing import Dict

from flock.resources.exceptions import AdmissionFailureError
from flock.resources.models import NodeResourceProfile


class AdmissionController:
    """Evaluates task parameters against quotas, limits, and node metrics."""

    def __init__(self, global_cpu_quota: float = 128.0) -> None:
        self.global_cpu_quota = global_cpu_quota

    def validate_admission(self, task_requirements: Dict[str, float], node: NodeResourceProfile) -> bool:
        """Validate if task requirements fit within quotas and metrics parameters.

        Raises:
            AdmissionFailureError: If quota checks or core bounds are exceeded.
        """
        requested_cpu = task_requirements.get("cpu", 0.0)
        
        # Check quota limits
        if requested_cpu > self.global_cpu_quota:
            raise AdmissionFailureError(f"Task CPU request '{requested_cpu}' exceeds global quota '{self.global_cpu_quota}'.")

        # Check node capability match
        if requested_cpu > node.cpu_cores:
            raise AdmissionFailureError(f"Task CPU request exceeds node total cores '{node.cpu_cores}'.")

        return True
