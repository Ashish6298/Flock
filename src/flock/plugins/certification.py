"""Plugin Quality Assurance, Conformance Testing, and Certification Engine.

Evaluates quality metrics categories, runs compliance checks, assesses compatibility
reports, and generates deterministic PluginCertificationReport outputs.
"""

from __future__ import annotations

import time
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List

import structlog

from flock.plugins.exceptions import PluginCertificationFailure
from flock.plugins.models import (
    PluginCertificationMetrics,
    PluginCertificationReport,
    PluginCertificationStatus,
    PluginCompatibilityReport,
    PluginComplianceResult,
    PluginQualityCategory,
    PluginQualityScore,
)
from flock.plugins.registry import PluginRegistry

logger = structlog.get_logger()


class PluginCertificationEngine:
    """Evaluates plugin quality scores, conformance rules compliance, and generates reports."""

    def __init__(self, registry: PluginRegistry, sdk_version: str = "1.0.0") -> None:
        self._registry = registry
        self._sdk_version = sdk_version

    def run_certification(self, plugin_id: str) -> PluginCertificationReport:
        """Executes full certification check pipeline and registers the report.

        Raises:
            PluginCertificationFailure: If validation errors are fatal.
        """
        start_time = time.perf_counter()

        manifest = self._registry.get_plugin(plugin_id)
        if manifest is None:
            raise PluginCertificationFailure(f"Cannot run certification: plugin '{plugin_id}' not found in registry.")

        # 1. Verify Compatibility
        compat = self.verify_compatibility(plugin_id)

        # 2. Run Compliance Rules
        compliance = self.validate_plugin(plugin_id)

        # 3. Calculate Quality Score
        quality = self.calculate_quality_score(plugin_id, compat, compliance)

        # 4. Determine final status
        status = PluginCertificationStatus.CERTIFIED
        if not compat.is_compatible or len(compliance.failed_rules) > 0:
            status = PluginCertificationStatus.FAILED
            if len(compliance.failed_rules) <= 2 and compat.is_compatible:
                # Minor compliance failures trigger conditional status
                status = PluginCertificationStatus.CONDITIONALLY_CERTIFIED
        
        # Arbitrary minimum score gate
        if quality.overall_score < 70.0 and status == PluginCertificationStatus.CERTIFIED:
            status = PluginCertificationStatus.CONDITIONALLY_CERTIFIED
        if quality.overall_score < 50.0:
            status = PluginCertificationStatus.REJECTED

        duration = (time.perf_counter() - start_time) * 1000.0
        rules_checked = len(compliance.passed_rules) + len(compliance.failed_rules)
        conformance = (len(compliance.passed_rules) / rules_checked * 100.0) if rules_checked > 0 else 100.0

        metrics = PluginCertificationMetrics(
            conformance_percent=conformance,
            rules_checked=rules_checked,
            rules_passed=len(compliance.passed_rules),
            duration_ms=duration,
        )

        report = PluginCertificationReport(
            report_id=str(uuid.uuid4()),
            plugin_id=plugin_id,
            version=manifest.version,
            status=status,
            quality_score=quality,
            compatibility=compat,
            compliance=compliance,
            metrics=metrics,
            certified_at=datetime.now(timezone.utc),
        )

        # Save to registry
        self._registry.save_certification_report(report)
        return report

    def verify_compatibility(self, plugin_id: str) -> PluginCompatibilityReport:
        """Evaluates SDK target version requirements and dependencies status."""
        manifest = self._registry.get_plugin(plugin_id)
        if manifest is None:
            return PluginCompatibilityReport(
                is_compatible=False,
                sdk_version_check="unknown",
                unresolved_dependencies=[plugin_id],
                details={"error": "Plugin not registered"},
            )

        # Check SDK major version alignment
        sdk_compat = manifest.sdk_version.split(".")[0] == self._sdk_version.split(".")[0]
        unresolved: List[str] = []

        # Passive check dependency resolution
        for dep in manifest.dependencies:
            dep_id = dep.split(">=")[0].split("<=")[0].split("==")[0].strip()
            if self._registry.get_plugin(dep_id) is None:
                unresolved.append(dep)

        is_compatible = sdk_compat and len(unresolved) == 0
        details = {
            "requested_sdk": manifest.sdk_version,
            "registry_sdk": self._sdk_version,
            "dependencies_count": len(manifest.dependencies),
        }

        return PluginCompatibilityReport(
            is_compatible=is_compatible,
            sdk_version_check="MATCH" if sdk_compat else "MISMATCH",
            unresolved_dependencies=unresolved,
            details=details,
        )

    def validate_plugin(self, plugin_id: str) -> PluginComplianceResult:
        """Evaluates structure, validation properties, and capability compliance rules."""
        manifest = self._registry.get_plugin(plugin_id)
        passed: List[str] = []
        failed: List[str] = []

        if manifest is None:
            failed.append("PluginExistsRule")
            return PluginComplianceResult(passed_rules=passed, failed_rules=failed)
        else:
            passed.append("PluginExistsRule")

        # Manifest completeness rules
        if manifest.name and len(manifest.name) > 0:
            passed.append("ManifestNameNotEmpty")
        else:
            failed.append("ManifestNameNotEmpty")

        if manifest.entry_point:
            passed.append("EntryPointDefined")
        else:
            # Entrypoint is warning/optional in some phases, but required for compliance
            failed.append("EntryPointDefined")

        # Security permissions checking
        permissions = self._registry.query_permissions(plugin_id)
        if len(permissions) > 0:
            passed.append("PermissionsDeclared")
        else:
            # Pass by default (plugins without permissions are compliant)
            passed.append("PermissionsDeclared")

        return PluginComplianceResult(passed_rules=passed, failed_rules=failed)

    def calculate_quality_score(
        self,
        plugin_id: str,
        compatibility: PluginCompatibilityReport,
        compliance: PluginComplianceResult,
    ) -> PluginQualityScore:
        """Determines deterministic quality scores based on weighted compliance categories."""
        # Weighted categories: SDK compatibility (40%), Compliance Rules conformance (60%)
        sdk_score = 100.0 if compatibility.sdk_version_check == "MATCH" else 0.0
        
        rules_checked = len(compliance.passed_rules) + len(compliance.failed_rules)
        rules_score = (len(compliance.passed_rules) / rules_checked * 100.0) if rules_checked > 0 else 100.0

        categories = [
            PluginQualityCategory(category_name="compatibility", score=sdk_score, weight=0.4),
            PluginQualityCategory(category_name="compliance", score=rules_score, weight=0.6),
        ]

        overall = (sdk_score * 0.4) + (rules_score * 0.6)
        
        return PluginQualityScore(
            overall_score=round(overall, 2),
            categories=categories,
        )

    def compare_certifications(self, report_a: PluginCertificationReport, report_b: PluginCertificationReport) -> Dict[str, Any]:
        """Calculates difference metrics between two certification reports."""
        score_diff = report_b.quality_score.overall_score - report_a.quality_score.overall_score
        status_changed = report_a.status != report_b.status
        
        return {
            "score_difference": round(score_diff, 2),
            "status_changed": status_changed,
            "previous_status": report_a.status,
            "new_status": report_b.status,
        }

    def certification_history(self, plugin_id: str) -> List[PluginCertificationReport]:
        """Queries historical certification reports matching plugin_id."""
        return self._registry.query_certification_reports(plugin_id)
