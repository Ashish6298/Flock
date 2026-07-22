"""Production readiness checklist auditor."""

from __future__ import annotations

import time
import threading
from typing import Dict, List
from flock.release.models import ReadinessAssessmentReport, SubsystemStatus


class ProductionReadinessAssessor:
    """Evaluates dependencies, config validation, and lifecycle states to assess production scores."""

    def __init__(self) -> None:
        self._lock = threading.RLock()

    def assess_readiness(
        self,
        version: str,
        dependencies_ok: bool,
        config_ok: bool,
        subsystems: List[SubsystemStatus],
    ) -> ReadinessAssessmentReport:
        """Run assessments and compile readiness report cards."""
        with self._lock:
            total_score = 0.0
            
            # 1. Check dependencies
            if dependencies_ok:
                total_score += 33.3
                
            # 2. Check configuration
            if config_ok:
                total_score += 33.3
                
            # 3. Check subsystems
            unhealthy = False
            for sub in subsystems:
                if sub.state in ("uninitialized", "degraded", "stopped"):
                    unhealthy = True
                    break
            
            subsystems_healthy = (not unhealthy and len(subsystems) > 0)
            if subsystems_healthy:
                total_score += 33.4
                
            return ReadinessAssessmentReport(
                timestamp=time.time(),
                manifest_version=version,
                dependency_status=dependencies_ok,
                configuration_status=config_ok,
                subsystems_healthy=subsystems_healthy,
                overall_readiness_score=round(total_score, 1),
            )
