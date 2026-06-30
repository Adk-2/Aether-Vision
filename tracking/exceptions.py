"""Exceptions raised by the tracking subsystem."""


class TrackingError(Exception):
    """Base exception for tracking subsystem failures."""


class AssociationError(TrackingError):
    """Raised when detections cannot be associated with tracks."""
