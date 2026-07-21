"""Command Formatter rendering tables, JSON, and YAML layout structures."""

from __future__ import annotations

import json
from typing import Any, Dict

from flock.cli.exceptions import OutputFormattingError
from flock.cli.models import OutputFormat


class CommandFormatter:
    """Serializes dataset mapping representations."""

    def __init__(self) -> None:
        pass

    def format_output(self, data: Dict[str, Any], format_spec: OutputFormat) -> str:
        """Convert payload to target string formats.

        Raises:
            OutputFormattingError: If conversion fails or target format is unsupported.
        """
        if format_spec.format_type == "json":
            try:
                return json.dumps(data)
            except Exception as exc:
                raise OutputFormattingError(f"JSON serialization failed: {exc}")
        elif format_spec.format_type == "yaml":
            # Simple simulation of YAML using key-value pair lines
            lines = [f"{k}: {v}" for k, v in data.items()]
            return "\n".join(lines)
        else:
            raise OutputFormattingError(f"Unsupported layout format '{format_spec.format_type}'.")
