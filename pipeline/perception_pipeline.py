"""Orchestration for one complete perception cycle."""

from time import perf_counter

from camera import CameraManager
from events import Event, EventEngine
from memory import MemoryEngine
from timeline import Timeline
from tracking import Tracker
from vision import DetectionAdapter, Renderer, VisionDetector
from world import WorldState

from .pipeline_result import PipelineResult

ZERO_FPS = 0.0


class PerceptionPipeline:
    """Own and orchestrate the perception subsystems."""

    def __init__(
        self,
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
        self.camera_manager = manager or CameraManager()
        self.vision_detector = detector or VisionDetector()
        self.detection_adapter = adapter or DetectionAdapter()
        self.renderer = renderer or Renderer()
        self.tracker = tracker or Tracker()
        self.world_state = world_state or WorldState()
        self.event_engine = event_engine or EventEngine()
        self.memory_engine = memory_engine or MemoryEngine()
        self.timeline = timeline or Timeline()

    def start(self) -> None:
        """Start resources required by the pipeline."""
        self.camera_manager.start()

    def process_next_frame(self) -> PipelineResult:
        """Run and return one complete perception cycle."""
        iteration_started = perf_counter()
        frame = self.camera_manager.read_frame()
        raw_results = self.vision_detector.detect(frame)
        detections = self.detection_adapter.convert(raw_results, frame.timestamp)
        tracks = self.tracker.update(detections)
        snapshot = self.world_state.update(tracks, frame.timestamp)
        events = self.event_engine.generate_events(
            self.world_state.previous_snapshot,
            snapshot,
        )
        self.memory_engine.process(events)
        self.timeline.process(events)
        self._print_events(events)
        fps = self._calculate_fps(iteration_started)
        should_quit = self.renderer.render(frame, tracks, fps)
        self._handle_shortcuts()
        return PipelineResult(frame, tracks, events, fps, should_quit)

    def close(self) -> None:
        """Release all resources owned by the pipeline."""
        self.camera_manager.stop()
        self.renderer.close()

    @staticmethod
    def _calculate_fps(iteration_started: float) -> float:
        elapsed_seconds = perf_counter() - iteration_started
        return 1.0 / elapsed_seconds if elapsed_seconds > 0.0 else ZERO_FPS

    @staticmethod
    def _print_events(events: list[Event]) -> None:
        for event in events:
            print(event.description)

    def _handle_shortcuts(self) -> None:
        if getattr(self.renderer, "memory_requested", False):
            self._print_memory()
        if getattr(self.renderer, "timeline_requested", False):
            self._print_timeline()

    def _print_memory(self) -> None:
        print("========== Working Memory ==========")
        records = self.memory_engine.store.list_all()
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

    def _print_timeline(self) -> None:
        print("========== Timeline =========")
        entries = self.timeline.store.all_entries()
        if not entries:
            print("(empty)")
        for entry in entries:
            print(f"\n#{entry.sequence_number}\n")
            print(entry.timestamp.strftime("%H:%M"))
            print(entry.description)
        print("=============================")
