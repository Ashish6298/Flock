"""Unit tests for InfrastructureTemplateEngine."""

import pytest
from flock.deployment.exceptions import InfrastructureExportError
from flock.deployment.models import DeploymentDefinition
from flock.deployment.templates import InfrastructureTemplateEngine


def test_template_spec_renders() -> None:
    engine = InfrastructureTemplateEngine()
    dep = DeploymentDefinition(
        deployment_id="dep-1",
        name="web-server",
        image="nginx:latest",
    )

    k8s = engine.render_kubernetes_spec(dep)
    assert "kind: Deployment" in k8s
    assert "name: web-server" in k8s

    compose = engine.render_docker_compose_spec(dep)
    assert "nginx:latest" in compose

    # Unnamed specs raise InfrastructureExportError
    dep_unnamed = DeploymentDefinition(
        deployment_id="dep-1",
        name="",
        image="nginx:latest",
    )
    with pytest.raises(InfrastructureExportError):
        engine.render_kubernetes_spec(dep_unnamed)
