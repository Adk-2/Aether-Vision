"""Working-memory exceptions."""


class MemoryError(Exception):
    """Base exception for working-memory failures."""


class MemoryQueryError(MemoryError):
    """Raised when a working-memory query cannot be completed."""
