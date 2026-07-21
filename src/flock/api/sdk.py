"""Python SDK Generator compiling client bindings."""

from __future__ import annotations

from typing import List

from flock.api.models import ApiRoute


class SdkGenerator:
    """Generates Python SDK bindings for cluster APIs."""

    def __init__(self) -> None:
        pass

    def generate_python_client(self, routes: List[ApiRoute]) -> str:
        """Construct Python SDK wrapper code string."""
        lines = [
            "import requests",
            "",
            "class FlockClient:",
            "    def __init__(self, endpoint: str, api_key: str) -> None:",
            "        self.endpoint = endpoint",
            "        self.headers = {'X-API-Key': api_key}",
            "",
        ]

        for route in routes:
            # Map route path to method name
            method_name = route.path.strip("/").replace("/", "_")
            if not method_name:
                method_name = "root"

            lines.extend([
                f"    def {method_name}(self) -> dict:",
                f"        res = requests.request('{route.method}', f'{{self.endpoint}}{route.path}', headers=self.headers)",
                "        return res.json()",
                "",
            ])

        return "\n".join(lines)
