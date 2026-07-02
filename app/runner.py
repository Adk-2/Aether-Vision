"""Application runner for the camera, vision, and tracking pipeline."""

from time import perf_counter

from camera import CameraManager
from events import EventEngine
from memory import MemoryEngine
from timeline import Timeline
from tracking import Tracker
from vision import DetectionAdapter, Renderer, VisionDetector
from world import WorldState

ZERO_FPS = 0.0


def run(
    manager: CameraManager | None = None,
    detector: VisionDetector | None = None,
    adapter: DetectionAdapter | None = None,
    renderer: Renderer | None = None,
    tracker: Tracker | None = None,
    world_state: WorldState | None = None,
    event_engine: EventEngine | None = None,
    memory_engine: MemoryEngine | None = None,
    timeline: Timeline | None = None,
) -> None:
    """Capture, detect, track, model changes, and render until Q is pressed."""
    camera_manager = manager or CameraManager()
    vision_detector = detector or VisionDetector()
    detection_adapter = adapter or DetectionAdapter()
    object_tracker = tracker or Tracker()
    current_world = world_state or WorldState()
    world_event_engine = event_engine or EventEngine()
    working_memory = memory_engine or MemoryEngine()
    episodic_timeline = timeline or Timeline()
    vision_renderer = renderer or Renderer()
    try:
        camera_manager.start()
        while True:
            iteration_started = perf_counter()
            frame = camera_manager.read_frame()
            raw_results = vision_detector.detect(frame)
            detections = detection_adapter.convert(raw_results, frame.timestamp)
            tracks = object_tracker.update(detections)
            snapshot = current_world.update(tracks, frame.timestamp)
            events = world_event_engine.generate_events(
                current_world.previous_snapshot,
                snapshot,
            )
            working_memory.process(events)
            episodic_timeline.process(events)
            for event in events:
                print(event.description)
            elapsed_seconds = perf_counter() - iteration_started
            fps = 1.0 / elapsed_seconds if elapsed_seconds > 0.0 else ZERO_FPS
            should_quit = vision_renderer.render(frame, tracks, fps)
            if getattr(vision_renderer, "memory_requested", False):
                _print_memory(working_memory)
            if getattr(vision_renderer, "timeline_requested", False):
                _print_timeline(episodic_timeline)
            if should_quit:
                break
    except KeyboardInterrupt:
        pass
    finally:
        camera_manager.stop()
        vision_renderer.close()


def _print_memory(memory_engine: MemoryEngine) -> None:
    """Print a formatted snapshot of current working memory."""
    print("========== Working Memory ==========")
    records = memory_engine.store.list_all()
    if not records:
        print("(empty)")
    for record in records:
        print(f"\n{record.object_name}\n")
        print(f"Status : {record.status.value}")
        print(f"Last Seen : {record.last_seen.isoformat()}")
        print(f"Position : {record.last_position}")
        print(f"History Entries : {len(record.history)}")
        print("------------------------------------")
    print("===================================")


def _print_timeline(timeline: Timeline) -> None:
    """Print the current episodic timeline."""
    print("========== Timeline =========")
    entries = timeline.store.all_entries()
    if not entries:
        print("(empty)")
    for entry in entries:
        print(f"\n#{entry.sequence_number}\n")
        print(entry.timestamp.strftime("%H:%M"))
        print(entry.description)
    print("=============================")
