"""Orchestration for one complete perception cycle."""

from collections.abc import Iterable
from time import perf_counter

from belief import BeliefEngine, BeliefState, alternatives
from camera import CameraManager
from events import Event, EventEngine, EventFilter
from identity import IdentityResolver, top_alternatives
from knowledge import KnowledgeEngine
from memory import MemoryEngine
from reasoning import (
    NearbyRelationshipRule,
    ReasoningEngine,
    RecentlyMovedRule,
    RuleRegistry,
    StationaryObjectRule,
)
from scene import SceneGraph, SceneGraphBuilder
from timeline import Timeline
from tracking import Track, Tracker
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
        event_filter: EventFilter | None = None,
        memory_engine: MemoryEngine | None = None,
        timeline: Timeline | None = None,
        scene_graph_builder: SceneGraphBuilder | None = None,
        identity_resolver: IdentityResolver | None = None,
        belief_engine: BeliefEngine | None = None,
        knowledge_engine: KnowledgeEngine | None = None,
        reasoning_engine: ReasoningEngine | None = None,
    ) -> None:
        self.camera_manager = manager or CameraManager()
        self.vision_detector = detector or VisionDetector()
        self.detection_adapter = adapter or DetectionAdapter()
        self.renderer = renderer or Renderer()
        self.tracker = tracker or Tracker()
        self.world_state = world_state or WorldState()
        self.event_engine = event_engine or EventEngine()
        self.event_filter = event_filter or EventFilter()
        self.memory_engine = memory_engine or MemoryEngine()
        self.timeline = timeline or Timeline()
        self.scene_graph_builder = scene_graph_builder or SceneGraphBuilder()
        self.scene_graph = SceneGraph()
        self.identity_resolver = identity_resolver or IdentityResolver()
        self.belief_engine = belief_engine or BeliefEngine()
        self.knowledge_engine = knowledge_engine or KnowledgeEngine(
            self.memory_engine,
            self.timeline,
            self.scene_graph,
            self.belief_engine,
        )
        self.reasoning_engine = reasoning_engine or ReasoningEngine(
            self.knowledge_engine,
            self._default_rule_registry(),
        )

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
        identities = self.identity_resolver.update(tracks)
        beliefs = self.belief_engine.update(identities)
        self._apply_beliefs(tracks, beliefs)
        snapshot = self.world_state.update(tracks, frame.timestamp)
        self.scene_graph = self.scene_graph_builder.build(tracks)
        self.knowledge_engine.use_scene_graph(self.scene_graph)
        generated_events = self.event_engine.generate_events(
            self.world_state.previous_snapshot,
            snapshot,
        )
        events = self.event_filter.filter_events(generated_events)
        self.memory_engine.process(events)
        self.timeline.process(events)
        self._print_events(events)
        fps = self._calculate_fps(iteration_started)
        should_quit = self.renderer.render(frame, tracks, fps)
        self._handle_shortcuts()
        return PipelineResult(
            frame=frame,
            tracks=tracks,
            events=events,
            fps=fps,
            should_quit=should_quit,
            scene_graph=self.scene_graph,
        )

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
        if getattr(self.renderer, "scene_graph_requested", False):
            self._print_scene_graph()
        if getattr(self.renderer, "identity_requested", False):
            self._print_identities()
        if getattr(self.renderer, "belief_requested", False):
            self._print_beliefs()
        if getattr(self.renderer, "knowledge_requested", False):
            self._print_knowledge()
        if getattr(self.renderer, "reasoning_requested", False):
            self._print_reasoning()

    @staticmethod
    def _default_rule_registry() -> RuleRegistry:
        registry = RuleRegistry()
        registry.register(StationaryObjectRule())
        registry.register(NearbyRelationshipRule())
        registry.register(RecentlyMovedRule())
        return registry

    def _print_reasoning(self) -> None:
        print("========== Reasoning ==========")
        snapshot = self.world_state.current_snapshot
        visible_ids = {
            track.track_id for track in snapshot.tracks
        } if snapshot is not None else set()
        records = [
            record
            for record in self.memory_engine.store.list_all()
            if record.track_id in visible_ids
        ]
        if not records:
            print("(empty)")
        for record in records:
            results = self.reasoning_engine.infer(record.object_name)
            print("\nObject\n")
            print(f"{self._display_object_name(record.object_name)}\n")
            print("Conclusions")
            if not results:
                print("\n(none)")
            for result in results:
                print(f"\n{result.conclusion}\n")
                print("Confidence\n")
                print(f"{result.confidence:.2f}")
            facts = self._unique_items(
                fact for result in results for fact in result.supporting_facts
            )
            print("\nFacts")
            if not facts:
                print("\n(none)")
            for fact in facts:
                print(f"\n{fact}")
            rules = self._unique_items(
                rule for result in results for rule in result.triggered_rules
            )
            print("\nTriggered Rules")
            if not rules:
                print("\n(none)")
            for rule in rules:
                print(f"\n{rule}")
        print("\n===============================")

    @staticmethod
    def _unique_items(items: Iterable[str]) -> list[str]:
        return list(dict.fromkeys(items))

    def _print_knowledge(self) -> None:
        print("========== Knowledge =========")
        records = self.memory_engine.store.list_all()
        if not records:
            print("(empty)")
        for record in records:
            name = record.object_name
            state = self.knowledge_engine.current_state(name)
            belief = self.knowledge_engine.current_belief(name)
            location = self.knowledge_engine.where_is(name)
            nearby = self.knowledge_engine.objects_near(name)
            history = self.knowledge_engine.what_happened(name)
            display_name = belief.result if belief.success else name
            print("\nObject\n")
            print(f"{display_name}\n")
            print("Current State\n")
            print(f"{state.result.value if state.success else '(unknown)'}\n")
            print("Belief\n")
            print(f"{belief.result if belief.success else '(unknown)'}\n")
            print("Confidence\n")
            confidence = belief.confidence
            print(f"{confidence:.2f}\n" if confidence is not None else "(unknown)\n")
            print("Location\n")
            print(f"{location.result if location.success else '(unknown)'}\n")
            print("Nearby")
            if not nearby.success or not nearby.result:
                print("\n(none)")
            else:
                for object_name in nearby.result:
                    print(f"\n{self._display_object_name(object_name)}")
            print("\n\nRecent Events")
            if not history.success or not history.result:
                print("\n(none)")
            else:
                for entry in history.result[-5:]:
                    print(f"\n{entry.event_type.value.title()}")
        print("\n==============================")

    @staticmethod
    def _display_object_name(object_name: str) -> str:
        label, separator, suffix = object_name.rpartition("_")
        return label if separator and suffix.isdigit() else object_name

    @staticmethod
    def _apply_beliefs(tracks: list[Track], beliefs: list[BeliefState]) -> None:
        """Expose stable beliefs to world-facing track consumers."""
        beliefs_by_track = {state.track_id: state for state in beliefs}
        for track in tracks:
            state = beliefs_by_track.get(track.track_id)
            if state is not None:
                track.stabilized_label = state.current_belief
                track.identity_confidence = state.confidence

    def _print_beliefs(self) -> None:
        print("========== Beliefs ==========")
        beliefs = self.belief_engine.all()
        if not beliefs:
            print("(empty)")
        for state in beliefs:
            print(f"\nTrack {state.track_id}\n")
            print("Current Belief\n")
            print(f"{state.current_belief}\n")
            print("Confidence\n")
            print(f"{state.confidence:.2f}\n")
            print("Frames Stable\n")
            print(f"{state.frames_stable}\n")
            print("Stable Since\n")
            print(f"{state.stable_since.strftime('%H:%M')}\n")
            print("Alternatives")
            ranked = alternatives(self.belief_engine, state.track_id)
            if not ranked:
                print("\n(none)")
            for label, _ in ranked:
                print(f"\n{label}")
        print("=============================")

    def _print_identities(self) -> None:
        print("========== Identity =========")
        identities = self.identity_resolver.all()
        if not identities:
            print("(empty)")
        for resolved in identities:
            print(f"\nTrack {resolved.track_id}\n")
            print("Current Label\n")
            print(f"{resolved.current_label}\n")
            print("Confidence\n")
            print(f"{resolved.confidence:.2f}\n")
            print("Alternatives")
            alternatives = top_alternatives(
                self.identity_resolver,
                resolved.track_id,
            )
            if not alternatives:
                print("\n(none)")
            for label, confidence in alternatives:
                print(f"\n{label}\n")
                print(f"{confidence:.2f}")
        print("================================")

    def _print_scene_graph(self) -> None:
        print("========== Scene Graph =========")
        relations = self.scene_graph.all_relations()
        if not relations:
            print("(empty)")
        for relation in relations:
            print(
                f"{relation.subject_name} "
                f"{relation.relation_type.value} "
                f"{relation.object_name}"
            )
        print("================================")

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
