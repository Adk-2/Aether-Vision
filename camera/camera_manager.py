"""Lifecycle management and frame creation for camera capture."""

from datetime import datetime, timezone
from typing import Any

from .camera import Camera
from .exceptions import CameraConnectionError, FrameCaptureError
from .frame import Frame

FIRST_FRAME_ID = 0
GRAYSCALE_CHANNELS = 1


class CameraManager:
    """Manage a camera and convert captured images into Frame objects."""

    def __init__(self, camera: Camera | None = None) -> None:
        """Initialize the manager with a camera or the default webcam."""
        self._camera = camera or Camera()
        self._next_frame_id = FIRST_FRAME_ID

    def start(self) -> None:
        """Start camera capture."""
        self._camera.open()

    def stop(self) -> None:
        """Stop camera capture and release its resources."""
        self._camera.close()

    def read_frame(self) -> Frame:
        """Capture and return the next canonical Frame."""
        if not self._camera.is_opened():
            raise CameraConnectionError("Camera manager has not been started")

        image = self._camera.read()
        height, width, channels = self._image_dimensions(image)
        frame = Frame(
            frame_id=self._next_frame_id,
            image=image,
            timestamp=datetime.now(timezone.utc),
            width=width,
            height=height,
            channels=channels,
        )
        self._next_frame_id += 1
        return frame

    @staticmethod
    def _image_dimensions(image: Any) -> tuple[int, int, int]:
        """Return height, width, and channel count for a captured image."""
        shape = getattr(image, "shape", None)
        if shape is None or len(shape) not in (2, 3):
            raise FrameCaptureError("Captured image has an invalid shape")

        height, width = shape[:2]
        channels = GRAYSCALE_CHANNELS if len(shape) == 2 else shape[2]
        return int(height), int(width), int(channels)
