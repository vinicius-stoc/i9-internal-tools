class PcpDomainError(Exception):
    """Base exception for expected PCP domain failures."""


class PcpValidationError(PcpDomainError):
    """Raised when a command violates a domain validation rule."""


class PcpConflictError(PcpDomainError):
    """Raised when a command conflicts with the current persisted state."""
