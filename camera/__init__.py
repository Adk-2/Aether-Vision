"""Camera capture interfaces for Project Aether."""

from .camera import Camera
from .camera_manager import CameraManager
from .exceptions import CameraConnectionError, CameraError, FrameCaptureError
from .frame import Frame

__all__ = [
    "Camera",
    "CameraConnectionError",
    "CameraError",
    "CameraManager",
    "Frame",
    "FrameCaptureError",
]
