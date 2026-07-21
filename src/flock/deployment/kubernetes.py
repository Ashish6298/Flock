"""Kubernetes Operator Engine compiling YAML manifests."""

from __future__ import annotations

from flock.deployment.models import DeploymentDefinition


class KubernetesOperatorEngine:
    """Compiles apps/v1 Deployments, Services, and CRD specs."""

    def __init__(self) -> None:
        pass

    def generate_manifests(self, deployment: DeploymentDefinition) -> str:
        """Create Kubernetes configuration descriptors string."""
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
