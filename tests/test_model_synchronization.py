"""Unit tests for ModelSynchronization."""

from flock.ai.models import ModelMetadata


def test_model_metadata_version_values() -> None:
    meta = ModelMetadata(version="1.2.0")
    assert meta.version == "1.2.0"
