"""CLI Subsystem Exceptions."""

from flock.exceptions import FlockError

class CommandNotFoundError(FlockError):
    """Raised when query action matches no command."""
    pass

class CommandExecutionError(FlockError):
    """Raised when runtime errors occur during command runs."""
    pass

class CommandValidationError(FlockError):
    """Raised when input parameters fail verification checks."""
    pass

class CommandPermissionError(FlockError):
    """Raised when security contexts reject executions permissions."""
    pass

class ProfileNotFoundError(FlockError):
    """Raised when profiles mappings cannot be matched."""
    pass

class ConfigurationError(FlockError):
    """Raised when context configs contain invalid files syntax."""
    pass

class SessionExpiredError(FlockError):
    """Raised when login metadata tokens lapse expiration limits."""
    pass

class AutocompleteError(FlockError):
    """Raised when autocompletion lists fail processing queries."""
    pass

class ContextSwitchError(FlockError):
    """Raised when selecting unrecognized target cluster contexts."""
    pass

class OutputFormattingError(FlockError):
    """Raised when layout formatter parses fail serialization."""
    pass

class ShellRuntimeError(FlockError):
    """Raised when prompt shells capture standard terminal exceptions."""
    pass
