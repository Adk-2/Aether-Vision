"""Exceptions raised by deterministic reasoning."""


class ReasoningError(Exception):
    """Base error raised by the reasoning subsystem."""


class RuleRegistrationError(ReasoningError):
    """Raised when an invalid rule is registered."""
