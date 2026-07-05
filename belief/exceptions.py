"""Exceptions raised by the belief subsystem."""


class BeliefError(Exception):
    """Base error raised while maintaining beliefs."""


class BeliefNotFoundError(BeliefError):
    """Raised when a belief is requested for an unknown track."""
