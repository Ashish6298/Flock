"""Init for cli package."""

from flock.cli.exceptions import (
    CommandNotFoundError,
    CommandExecutionError,
    CommandValidationError,
    CommandPermissionError,
    ProfileNotFoundError,
    ConfigurationError,
    SessionExpiredError,
    AutocompleteError,
    ContextSwitchError,
    OutputFormattingError,
    ShellRuntimeError,
)
from flock.cli.models import (
    CommandDefinition,
    CommandRequest,
    CommandResponse,
    CommandContext,
    ExecutionResult,
    ExecutionProgress,
    SessionMetadata,
    ProfileDefinition,
    ConfigurationModel,
    CompletionCandidate,
    CommandHistory,
    OutputFormat,
    ClusterContext,
    AuthenticationContext,
    CliMetrics,
    CliStatistics,
)
from flock.cli.commands import CommandRegistry
from flock.cli.parser import CommandParser
from flock.cli.shell import ReplEngine
from flock.cli.completion import AutoCompleteEngine
from flock.cli.formatter import CommandFormatter
from flock.cli.configuration import ConfigurationManager
from flock.cli.profiles import ProfileManager
from flock.cli.history import HistoryLogger
from flock.cli.session import SessionManager
from flock.cli.executor import CommandExecutionEngine
from flock.cli.service import CliService
from flock.cli.main import main

__all__ = [
    "main",
    "CommandNotFoundError",
    "CommandExecutionError",
    "CommandValidationError",
    "CommandPermissionError",
    "ProfileNotFoundError",
    "ConfigurationError",
    "SessionExpiredError",
    "AutocompleteError",
    "ContextSwitchError",
    "OutputFormattingError",
    "ShellRuntimeError",
    "CommandDefinition",
    "CommandRequest",
    "CommandResponse",
    "CommandContext",
    "ExecutionResult",
    "ExecutionProgress",
    "SessionMetadata",
    "ProfileDefinition",
    "ConfigurationModel",
    "CompletionCandidate",
    "CommandHistory",
    "OutputFormat",
    "ClusterContext",
    "AuthenticationContext",
    "CliMetrics",
    "CliStatistics",
    "CommandRegistry",
    "CommandParser",
    "ReplEngine",
    "AutoCompleteEngine",
    "CommandFormatter",
    "ConfigurationManager",
    "ProfileManager",
    "HistoryLogger",
    "SessionManager",
    "CommandExecutionEngine",
    "CliService",
]
