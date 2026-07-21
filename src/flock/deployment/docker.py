"""Docker Deployment Engine compiling compose configurations."""

from __future__ import annotations

from flock.deployment.models import DeploymentDefinition


class DockerDeploymentEngine:
    """Compiles container configurations and docker compose overrides."""

    def __init__(self) -> None:
        pass

    def generate_compose_file(self, deployment: DeploymentDefinition) -> str:
        """Create docker compose file content string."""
        return f"""version: '3.8'
services:
  {deployment.name}:
    image: {deployment.image}
    environment:
      - FLOCK_NAMESPACE={deployment.namespace}
    deploy:
      replicas: {deployment.replicas}
"""
