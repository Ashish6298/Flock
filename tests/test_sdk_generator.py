"""Unit tests for SdkGenerator."""

from flock.api.models import ApiRoute
from flock.api.sdk import SdkGenerator


def test_sdk_python_client_generation() -> None:
    generator = SdkGenerator()

    routes = [
        ApiRoute(path="/tasks", method="GET", handler_name="get_tasks"),
    ]

    client_code = generator.generate_python_client(routes)
    
    assert "class FlockClient:" in client_code
    assert "def tasks(self) -> dict:" in client_code
    assert "requests.request('GET'" in client_code
