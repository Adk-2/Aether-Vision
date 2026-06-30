"""Application runner for the camera, vision, and tracking pipeline."""

from time import perf_counter

from camera import CameraManager
from tracking import Tracker
from vision import DetectionAdapter, Renderer, VisionDetector

ZERO_FPS = 0.0


def run(
    manager: CameraManager | None = None,
    detector: VisionDetector | None = None,
    adapter: DetectionAdapter | None = None,
    renderer: Renderer | None = None,
    tracker: Tracker | None = None,
) -> None:
    """Capture, detect, track, and render frames until Q is pressed."""
    camera_manager = manager or CameraManager()
    vision_detector = detector or VisionDetector()
    detection_adapter = adapter or DetectionAdapter()
    object_tracker = tracker or Tracker()
    vision_renderer = renderer or Renderer()
    try:
        camera_manager.start()
        while True:
            iteration_started = perf_counter()
            frame = camera_manager.read_frame()
            raw_results = vision_detector.detect(frame)
            detections = detection_adapter.convert(raw_results, frame.timestamp)
            tracks = object_tracker.update(detections)
            elapsed_seconds = perf_counter() - iteration_started
            fps = 1.0 / elapsed_seconds if elapsed_seconds > 0.0 else ZERO_FPS
            if vision_renderer.render(frame, tracks, fps):
                break
    except KeyboardInterrupt:
        pass
    finally:
        camera_manager.stop()
        vision_renderer.close()
