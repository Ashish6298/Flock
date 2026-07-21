"""OpenAPI spec generator compiling Swagger manifests."""

from __future__ import annotations

from typing import List

from flock.api.models import ApiRoute, OpenApiDocument


class OpenApiGenerator:
    """Extracts registered endpoints to generate OpenAPI schemas."""

    def __init__(self, title: str = "Flock API", version: str = "1.0.0") -> None:
        self.title = title
        self.version = version

    def generate_document(self, routes: List[ApiRoute]) -> OpenApiDocument:
        """Compile OpenAPI paths lists."""
        paths = []
        for r in routes:
            paths.append(f"{r.method.upper()} {r.path}")

        return OpenApiDocument(
            title=self.title,
            version=self.version,
            info={"description": "Generated Flock Cluster Endpoint specs"},
            paths=paths,
        )
