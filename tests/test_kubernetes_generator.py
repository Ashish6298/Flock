"""Unit tests for KubernetesOperatorEngine Pydantic specs and validators."""

import pytest
from flock.deployment.models import DeploymentDefinition
from flock.deployment.kubernetes import (
    KubernetesOperatorEngine,
    K8sValidator,
    K8sDeployment,
    K8sDeploymentSpec,
    K8sMetadata,
    K8sContainer,
    K8sResourceLimits,
    K8sProbe,
    K8sService,
    K8sServiceSpec,
    K8sConfigMap,
    K8sSecret,
    K8sPVC,
    K8sPVCSpec,
)


def test_kubernetes_manifest_generation() -> None:
    engine = KubernetesOperatorEngine()
    dep = DeploymentDefinition(
        deployment_id="dep-k8s",
        name="api-gateway",
        namespace="prod",
        image="gateway:v2",
        replicas=3,
    )

    manifests = engine.generate_manifests(dep)
    assert "kind: Deployment" in manifests
    assert "kind: Service" in manifests
    assert "name: api-gateway-deployment" in manifests
    assert "namespace: prod" in manifests
    assert "replicas: 3" in manifests


def test_k8s_deployment_generation_and_validation() -> None:
    engine = KubernetesOperatorEngine()
    
    meta = K8sMetadata(
        name="worker-deployment",
        namespace="staging",
        labels={"app": "flock-worker"},
    )
    res = K8sResourceLimits(
        cpu_request="50m",
        cpu_limit="100m",
        memory_request="64Mi",
        memory_limit="128Mi",
    )
    probe = K8sProbe(
        exec_command=["flock", "diagnostics"],
        initial_delay_seconds=5,
    )
    container = K8sContainer(
        name="flock-container",
        image="flock-node:latest",
        ports=[8080],
        resources=res,
        liveness_probe=probe,
    )
    spec = K8sDeploymentSpec(
        replicas=2,
        selector={"app": "flock-worker"},
        containers=[container],
    )
    deployment = K8sDeployment(
        metadata=meta,
        spec=spec,
    )

    # Validate
    val_res = K8sValidator.validate_deployment(deployment)
    assert val_res.is_valid is True
    assert len(val_res.errors) == 0

    # Compile
    yaml_out = engine.generate_deployment_manifest(deployment)
    assert "kind: Deployment" in yaml_out
    assert "name: worker-deployment" in yaml_out
    assert "cpu_limit: 100m" in yaml_out
    assert "initial_delay_seconds: 5" in yaml_out


def test_k8s_validation_errors() -> None:
    # 1. Invalid short name & negative replicas
    meta = K8sMetadata(name="ws", labels={"app": "web"})
    spec = K8sDeploymentSpec(
        replicas=-1,
        selector={"app": "web"},
        containers=[],
    )
    deployment = K8sDeployment(metadata=meta, spec=spec)
    val_res = K8sValidator.validate_deployment(deployment)
    assert val_res.is_valid is False
    assert any("name must be at least 3 characters" in err for err in val_res.errors)
    assert any("Replica count cannot be negative" in err for err in val_res.errors)

    # 2. Selector tag mismatch
    meta_mismatch = K8sMetadata(name="web-deployment", labels={"app": "web-mismatch"})
    spec_mismatch = K8sDeploymentSpec(
        replicas=1,
        selector={"app": "web"},
        containers=[],
    )
    dep_mismatch = K8sDeployment(metadata=meta_mismatch, spec=spec_mismatch)
    val_res_mismatch = K8sValidator.validate_deployment(dep_mismatch)
    assert val_res_mismatch.is_valid is False
    assert any("must match deployment metadata labels" in err for err in val_res_mismatch.errors)


def test_k8s_supporting_resources_generation() -> None:
    engine = KubernetesOperatorEngine()
    meta = K8sMetadata(name="flock-config", namespace="prod")

    # Service
    svc = K8sService(
        metadata=meta,
        spec=K8sServiceSpec(
            ports=[{"port": 80, "targetPort": 8080}],
            selector={"app": "flock-node"},
        )
    )
    assert "kind: Service" in engine.generate_service_manifest(svc)

    # ConfigMap
    cm = K8sConfigMap(
        metadata=meta,
        data={"FLOCK_ENV": "production"},
    )
    assert "FLOCK_ENV: production" in engine.generate_configmap_manifest(cm)

    # Secret
    sec = K8sSecret(
        metadata=meta,
        data={"api-key": "c3VwZXJzZWNyZXQ="},
    )
    assert "kind: Secret" in engine.generate_secret_manifest(sec)

    # PVC
    pvc = K8sPVC(
        metadata=meta,
        spec=K8sPVCSpec(storage_size="10Gi"),
    )
    assert "storage_size: 10Gi" in engine.generate_pvc_manifest(pvc)
