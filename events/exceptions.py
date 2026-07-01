"""Exceptions raised while modeling and comparing world state."""


class EventError(Exception):
    """Base error raised by event detection."""


class WorldStateError(Exception):
    """Raised when a valid world snapshot cannot be created."""
