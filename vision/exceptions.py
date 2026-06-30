"""Exceptions raised by the vision subsystem."""


class VisionError(Exception):
    """Base exception for vision subsystem failures."""


class ModelLoadError(VisionError):
    """Raised when a vision model cannot be loaded."""


class InferenceError(VisionError):
    """Raised when the vision model cannot process a frame."""
