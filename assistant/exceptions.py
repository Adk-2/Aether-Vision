"""Exceptions raised by the assistant interface."""


class AssistantError(Exception):
    """Base exception for assistant orchestration errors."""


class QueryParseError(AssistantError):
    """Raised when a query cannot be parsed into a supported pattern."""


class UnsupportedIntentError(AssistantError):
    """Raised when no deterministic handler exists for an intent."""
