"""OpenCV-backed camera access."""

from typing import Any

import cv2

from .exceptions import CameraConnectionError, FrameCaptureError

DEFAULT_CAMERA_INDEX = 0


class Camera:
    """Open, close, and read images from one camera source."""

    def __init__(self, source: int | str = DEFAULT_CAMERA_INDEX) -> None:
        """Initialize a camera for the given OpenCV-compatible source."""
        self._source = source
        self._capture: cv2.VideoCapture | None = None

    def open(self) -> None:
        """Open the configured camera source."""
        if self.is_opened():
            return

        self.close()
        capture = cv2.VideoCapture(self._source)
        if not capture.isOpened():
            capture.release()
            raise CameraConnectionError(
                f"Unable to open camera source: {self._source!r}"
            )
        self._capture = capture

    def close(self) -> None:
        """Release the camera source if it is open."""
        if self._capture is not None:
            self._capture.release()
            self._capture = None

    def read(self) -> Any:
        """Read and return one raw image from the open camera."""
        if not self.is_opened() or self._capture is None:
            raise CameraConnectionError("Camera is not open")

        success, image = self._capture.read()
        if not success or image is None:
            raise FrameCaptureError("Unable to capture a frame")
        return image

    def is_opened(self) -> bool:
        """Return whether the camera source is currently open."""
        return self._capture is not None and self._capture.isOpened()
