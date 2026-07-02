"""Episodic timeline exceptions."""


class TimelineError(Exception):
    """Base exception for timeline failures."""


class TimelineQueryError(TimelineError):
    """Raised when a timeline query cannot be completed."""
