"""Unit tests for KubernetesOperatorEngine."""

from flock.deployment.models import DeploymentDefinition
from flock.deployment.kubernetes import KubernetesOperatorEngine


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
