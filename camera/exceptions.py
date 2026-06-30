"""Exceptions raised by the camera subsystem."""


class CameraError(Exception):
    """Base exception for camera subsystem failures."""


class CameraConnectionError(CameraError):
    """Raised when a camera cannot be opened or is unavailable."""


class FrameCaptureError(CameraError):
    """Raised when a frame cannot be captured or interpreted."""
