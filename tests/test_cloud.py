"""Unit tests for Cloud deployment engine and package validator."""

import pytest
from flock.deployment.models import DeploymentDefinition
from flock.deployment.cloud import (
    CloudProfile,
    CloudDeploymentEngine,
    CloudPackageValidator,
)


def test_cloud_deployment_packaging() -> None:
    engine = CloudDeploymentEngine()
    dep = DeploymentDefinition(
        deployment_id="dep-cloud-1",
        name="auth-service",
        image="auth:v1",
        replicas=2,
    )
    profile = CloudProfile(
        provider="aws",
        region="us-west-2",
        instance_type="t3.medium",
    )

    # 1. Compile Package
    pkg = engine.compile_package(dep, profile, k8s_manifests="apiVersion: v1", docker_compose="version: '3'")
    assert pkg.package_id == "pkg-dep-cloud-1"
    assert "kubernetes" in pkg.manifest_files
    assert "docker-compose" in pkg.manifest_files
    assert len(pkg.integrity_hash) == 64

    # 2. Verify integrity
    assert CloudPackageValidator.verify_integrity(pkg) is True

    # 3. Tamper detection
    tampered_pkg = pkg.model_copy(update={"integrity_hash": "corrupted"})
    assert CloudPackageValidator.verify_integrity(tampered_pkg) is False
