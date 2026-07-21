"""Unit tests for OpenApiGenerator."""

from flock.api.models import ApiRoute
from flock.api.openapi import OpenApiGenerator


def test_openapi_manifest_generation() -> None:
    generator = OpenApiGenerator(title="Flock Core API", version="2.0.0")
    
    routes = [
        ApiRoute(path="/tasks", method="GET", handler_name="get_tasks"),
        ApiRoute(path="/jobs", method="POST", handler_name="create_job"),
    ]

    doc = generator.generate_document(routes)
    
    assert doc.title == "Flock Core API"
    assert doc.version == "2.0.0"
    assert "GET /tasks" in doc.paths
    assert "POST /jobs" in doc.paths
