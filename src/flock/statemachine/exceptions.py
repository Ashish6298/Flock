"""StateMachine exceptions."""

from flock.exceptions import FlockError

class StateMachineError(FlockError):
    """Base exception for all StateMachine errors."""
    pass

class DuplicateCommandError(StateMachineError):
    """Raised when a command is submitted that has already been executed."""
    pass

class CommandValidationError(StateMachineError):
    """Raised when command payload validation fails."""
    pass

class StateConflictError(StateMachineError):
    """Raised when an operation conflicts with the current state (e.g. UPDATE on missing key)."""
    pass

class SnapshotVersionError(StateMachineError):
    """Raised when snapshot restoration detects incompatible indices or terms."""
    pass

class UnknownStateKeyError(StateMachineError):
    """Raised when requesting a key that does not exist in the store."""
    pass
