"""DataGrid Subsystem Exceptions."""

from flock.exceptions import FlockError

class DataGridError(FlockError):
    """Base exception for all datagrid operations."""
    pass

class RecordNotFoundError(DataGridError):
    """Raised when request references missing KV key."""
    pass

class IndexValidationError(DataGridError):
    """Raised when secondary indexes configuration fails schema check."""
    pass

class LockAcquisitionError(DataGridError):
    """Raised when lease client fails to acquire key mutex lock."""
    pass

class BucketQuotaExceededError(DataGridError):
    """Raised when object payload exceeds bucket quota limits."""
    pass

class ReplicationSyncError(DataGridError):
    """Raised when peer state synchronization handshake fails."""
    pass
