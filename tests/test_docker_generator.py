"""Unit tests for DockerDeploymentEngine."""

from flock.deployment.models import DeploymentDefinition
from flock.deployment.docker import DockerDeploymentEngine


def test_docker_compose_manifest_generation() -> None:
    engine = DockerDeploymentEngine()
    dep = DeploymentDefinition(
        deployment_id="dep-docker",
        name="worker-node",
        namespace="staging",
        image="flock-worker:latest",
        replicas=2,
    )

    compose_content = engine.generate_compose_file(dep)
    assert "version: '3.8'" in compose_content
    assert "image: flock-worker:latest" in compose_content
    assert "replicas: 2" in compose_content
    assert "FLOCK_NAMESPACE=staging" in compose_content
