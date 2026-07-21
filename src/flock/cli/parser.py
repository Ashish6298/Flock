"""Command Parser supporting nested command lines."""

from __future__ import annotations

from typing import List

from flock.cli.exceptions import CommandValidationError


class CommandParser:
    """Tokenizes string lines into arguments arrays."""

    def __init__(self) -> None:
        pass

    def parse(self, command_line: str) -> List[str]:
        """Convert input to token items list.

        Raises:
            CommandValidationError: If command line parameter is empty.
        """
        clean = command_line.strip()
        if not clean:
            raise CommandValidationError("Cannot parse empty command lines.")

        # Simple space tokenizer ignoring quotes logic for basic CLI parsing
        return clean.split()
