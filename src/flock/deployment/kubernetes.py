"""Kubernetes Operator Engine compiling YAML manifests."""

from __future__ import annotations

import time
from typing import Dict, List, Optional
from pydantic import BaseModel, Field

from flock.deployment.models import DeploymentDefinition


class K8sMetadata(BaseModel):
    """Kubernetes resource metadata specs."""
    name: str
    namespace: str = "default"
    labels: Dict[str, str] = Field(default_factory=dict)
    annotations: Dict[str, str] = Field(default_factory=dict)

    model_config = {"frozen": True}


class K8sResourceLimits(BaseModel):
    """Kubernetes resource limits requirements details."""
    cpu_request: Optional[str] = None
    cpu_limit: Optional[str] = None
    memory_request: Optional[str] = None
    memory_limit: Optional[str] = None

    model_config = {"frozen": True}


class K8sProbe(BaseModel):
    """Kubernetes pod liveness and readiness check spec configurations."""
    exec_command: List[str] = Field(default_factory=list)
    initial_delay_seconds: int = 0
    period_seconds: int = 10
    timeout_seconds: int = 1
    failure_threshold: int = 3

    model_config = {"frozen": True}


class K8sContainer(BaseModel):
    """Kubernetes container definition details."""
    name: str
    image: str
    ports: List[int] = Field(default_factory=list)
    env: Dict[str, str] = Field(default_factory=dict)
    resources: K8sResourceLimits = Field(default_factory=K8sResourceLimits)
    liveness_probe: Optional[K8sProbe] = None
    readiness_probe: Optional[K8sProbe] = None

    model_config = {"frozen": True}


class K8sDeploymentSpec(BaseModel):
    """Kubernetes Deployment specifications definition."""
    replicas: int = 1
    selector: Dict[str, str] = Field(default_factory=dict)
    containers: List[K8sContainer] = Field(default_factory=list)

    model_config = {"frozen": True}


class K8sDeployment(BaseModel):
    """Deployment representation wrapper."""
    api_version: str = "apps/v1"
    kind: str = "Deployment"
    metadata: K8sMetadata
    spec: K8sDeploymentSpec

    model_config = {"frozen": True}


class K8sServiceSpec(BaseModel):
    """Kubernetes Service specifications mapping."""
    ports: List[Dict[str, int]] = Field(default_factory=list)  # port, targetPort
    selector: Dict[str, str] = Field(default_factory=dict)
    type: str = "ClusterIP"

    model_config = {"frozen": True}


class K8sService(BaseModel):
    """Service representation wrapper."""
    api_version: str = "v1"
    kind: str = "Service"
    metadata: K8sMetadata
    spec: K8sServiceSpec

    model_config = {"frozen": True}


class K8sConfigMap(BaseModel):
    """ConfigMap data records blueprints."""
    api_version: str = "v1"
    kind: str = "ConfigMap"
    metadata: K8sMetadata
    data: Dict[str, str] = Field(default_factory=dict)

    model_config = {"frozen": True}


class K8sSecret(BaseModel):
    """Secret data records bindings details."""
    api_version: str = "v1"
    kind: str = "Secret"
    metadata: K8sMetadata
    data: Dict[str, str] = Field(default_factory=dict)
    type: str = "Opaque"

    model_config = {"frozen": True}


class K8sPVCSpec(BaseModel):
    """PersistentVolumeClaim access constraints settings."""
    access_modes: List[str] = Field(default_factory=lambda: ["ReadWriteOnce"])
    storage_class_name: Optional[str] = None
    storage_size: str

    model_config = {"frozen": True}


class K8sPVC(BaseModel):
    """PersistentVolumeClaim spec configuration model."""
    api_version: str = "v1"
    kind: str = "PersistentVolumeClaim"
    metadata: K8sMetadata
    spec: K8sPVCSpec

    model_config = {"frozen": True}


# ------------------------------------------------------------------
# Kubernetes Validator
# ------------------------------------------------------------------

class K8sValidationResult(BaseModel):
    """Validation report status codes details."""
    is_valid: bool
    errors: List[str] = Field(default_factory=list)

    model_config = {"frozen": True}


class K8sValidator:
    """Kubernetes configuration constraint validator."""

    @staticmethod
    def validate_deployment(deployment: K8sDeployment) -> K8sValidationResult:
        """Validate naming specs, replica ranges, selector tags, and port values."""
        errors: List[str] = []
        meta = deployment.metadata
        spec = deployment.spec

        # 1. Naming validations
        if not meta.name or len(meta.name) < 3:
            errors.append("Resource name must be at least 3 characters long.")

        # 2. Replicas validations
        if spec.replicas < 0:
            errors.append("Replica count cannot be negative.")

        # 3. Label/Selector checks
        for k, v in spec.selector.items():
            if k not in meta.labels or meta.labels[k] != v:
                errors.append(f"Selector key/value '{k}:{v}' must match deployment metadata labels.")

        # 4. Port ranges checks
        for container in spec.containers:
            for p in container.ports:
                if p < 1 or p > 65535:
                    errors.append(f"Port {p} is out of valid range (1-65535).")

        return K8sValidationResult(
            is_valid=len(errors) == 0,
            errors=errors
        )


# ------------------------------------------------------------------
# Kubernetes Operator Engine
# ------------------------------------------------------------------

class KubernetesOperatorEngine:
    """Compiles apps/v1 Deployments, Services, and CRD specs."""

    def __init__(self) -> None:
        pass

    def generate_manifests(self, deployment: DeploymentDefinition) -> str:
        """Create Kubernetes configuration descriptors string (Legacy compatibility)."""
        return f"""apiVersion: apps/v1
kind: Deployment
metadata:
  name: {deployment.name}-deployment
  namespace: {deployment.namespace}
spec:
  replicas: {deployment.replicas}
  template:
    spec:
      containers:
      - name: app
        image: {deployment.image}
---
apiVersion: v1
kind: Service
metadata:
  name: {deployment.name}-service
  namespace: {deployment.namespace}
spec:
  ports:
  - port: 80
  selector:
    app: {deployment.name}
"""

    def generate_deployment_manifest(self, k8s_dep: K8sDeployment) -> str:
        """Convert K8sDeployment spec into deterministic sorted YAML string."""
        from flock.deployment.docker import to_yaml
        return to_yaml(k8s_dep.model_dump())

    def generate_service_manifest(self, k8s_svc: K8sService) -> str:
        """Convert K8sService spec into deterministic sorted YAML string."""
        from flock.deployment.docker import to_yaml
        return to_yaml(k8s_svc.model_dump())

    def generate_configmap_manifest(self, k8s_cm: K8sConfigMap) -> str:
        """Convert K8sConfigMap spec into deterministic sorted YAML string."""
        from flock.deployment.docker import to_yaml
        return to_yaml(k8s_cm.model_dump())

    def generate_secret_manifest(self, k8s_sec: K8sSecret) -> str:
        """Convert K8sSecret spec into deterministic sorted YAML string."""
        from flock.deployment.docker import to_yaml
        return to_yaml(k8s_sec.model_dump())

    def generate_pvc_manifest(self, k8s_pvc: K8sPVC) -> str:
        """Convert K8sPVC spec into deterministic sorted YAML string."""
        from flock.deployment.docker import to_yaml
        return to_yaml(k8s_pvc.model_dump())
