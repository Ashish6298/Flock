"""Cloud deployment templates packaging engine."""

from __future__ import annotations

import hashlib
from typing import Dict, List, Optional
from pydantic import BaseModel, Field

from flock.deployment.models import DeploymentDefinition


class CloudProfile(BaseModel):
    """Configuration mapping regions and node constraints."""
    provider: str
    region: str
    instance_type: str

    model_config = {"frozen": True}


class CloudDeploymentPackage(BaseModel):
    """Distribution bundle containing descriptors and integrity hashes."""
    package_id: str
    manifest_files: Dict[str, str] = Field(default_factory=dict)
    integrity_hash: str

    model_config = {"frozen": True}


class CloudDeploymentEngine(BaseModel):
    """Compiles multi-provider deployment bundles."""

    def compile_package(
        self,
        deployment: DeploymentDefinition,
        profile: CloudProfile,
        k8s_manifests: str = "",
        docker_compose: str = "",
    ) -> CloudDeploymentPackage:
        """deterministic deployment package creation."""
        manifests = {
            "app-deployment": f"image: {deployment.image}\nreplicas: {deployment.replicas}",
            "cloud-profile": f"provider: {profile.provider}\nregion: {profile.region}",
        }
        if k8s_manifests:
            manifests["kubernetes"] = k8s_manifests
        if docker_compose:
            manifests["docker-compose"] = docker_compose

        # Deterministic hashing of keys and values
        sorted_keys = sorted(manifests.keys())
        hash_src = "".join(f"{k}:{manifests[k]}" for k in sorted_keys)
        integrity_hash = hashlib.sha256(hash_src.encode("utf-8")).hexdigest()

        return CloudDeploymentPackage(
            package_id=f"pkg-{deployment.deployment_id}",
            manifest_files=manifests,
            integrity_hash=integrity_hash,
        )


class CloudPackageValidator:
    """Artifact integrity checking framework."""

    @staticmethod
    def verify_integrity(package: CloudDeploymentPackage) -> bool:
        """Verifies package integrity checks against checksum values."""
        sorted_keys = sorted(package.manifest_files.keys())
        hash_src = "".join(f"{k}:{package.manifest_files[k]}" for k in sorted_keys)
        expected_hash = hashlib.sha256(hash_src.encode("utf-8")).hexdigest()
        return package.integrity_hash == expected_hash
