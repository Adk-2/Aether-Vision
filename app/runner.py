"""Application runner for continuous camera capture."""

import os
import select
import sys
from collections.abc import Callable

from camera import CameraError, CameraManager, Frame

QUIT_KEY = "q"


def _quit_requested() -> bool:
    """Return whether Q has been pressed without blocking capture."""
    if os.name == "nt":
        import msvcrt

        if not msvcrt.kbhit():
            return False
        return msvcrt.getwch().lower() == QUIT_KEY

    readable, _, _ = select.select([sys.stdin], [], [], 0)
    if not readable:
        return False
    return sys.stdin.read(1).lower() == QUIT_KEY


def _print_frame(frame: Frame) -> None:
    """Print the required identifying information for a frame."""
    print(
        f"Frame ID: {frame.frame_id} | "
        f"Resolution: {frame.width}x{frame.height} | "
        f"Timestamp: {frame.timestamp.isoformat()}"
    )


def run(
    manager: CameraManager | None = None,
    quit_requested: Callable[[], bool] = _quit_requested,
) -> None:
    """Capture frames continuously until Q is pressed."""
    camera_manager = manager or CameraManager()
    try:
        camera_manager.start()
        while not quit_requested():
            _print_frame(camera_manager.read_frame())
    except CameraError as error:
        print(f"Camera error: {error}", file=sys.stderr)
    except KeyboardInterrupt:
        pass
    finally:
        camera_manager.stop()
