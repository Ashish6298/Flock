"""Typed exceptions for Policy-as-Code and compliance orchestration framework."""

from flock.exceptions import FlockError

class PolicyError(FlockError):
    """Base exception for all Policy-as-Code and governance operations."""
    pass

class PolicyCompilationError(PolicyError):
    """Raised when policy schema validation or rules compilation fails."""
    pass

class PolicyEvaluationError(PolicyError):
    """Raised when policy evaluation rules fail to execute or raise syntax issues."""
    pass

class ComplianceAssessmentError(PolicyError):
    """Raised when running compliance framework audits fails."""
    pass

class PolicySyncError(PolicyError):
    """Raised when synchronizing policies between federated clusters fails."""
    pass

class ApprovalWorkflowError(PolicyError):
    """Raised when policy approval steps or exceptions management fail."""
    pass
