"""Infrastructure Template Engine converting blueprints to config."""

from __future__ import annotations

from flock.deployment.exceptions import InfrastructureExportError
from flock.deployment.models import DeploymentDefinition, InfrastructureTemplate


class InfrastructureTemplateEngine:
    """Renders Docker and Kubernetes manifests from metadata definitions."""

    def __init__(self) -> None:
        pass

    def render_kubernetes_spec(self, deployment: DeploymentDefinition) -> str:
        """Compile deployment spec to Kubernetes manifest string."""
        if not deployment.name.strip():
            raise InfrastructureExportError("Service name cannot be empty.")

        return f"""apiVersion: apps/v1
kind: Deployment
metadata:
  name: {deployment.name}
  namespace: {deployment.namespace}
spec:
  replicas: {deployment.replicas}
  selector:
    matchLabels:
      app: {deployment.name}
  template:
    metadata:
      labels:
        app: {deployment.name}
    spec:
      containers:
      - name: container
        image: {deployment.image}
"""

    def render_docker_compose_spec(self, deployment: DeploymentDefinition) -> str:
        """Compile deployment spec to Docker Compose manifest string."""
        return f"""version: '3.8'
services:
  {deployment.name}:
    image: {deployment.image}
    deploy:
      replicas: {deployment.replicas}
"""
