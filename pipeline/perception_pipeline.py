"""Orchestration for one complete perception cycle."""

from collections import deque
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime
from time import perf_counter

from assistant import Assistant, QueryEngine
from belief import BeliefEngine, BeliefState, alternatives
from camera import CameraManager
from events import Event, EventEngine, EventFilter
from identity import IdentityResolver, top_alternatives
from knowledge import KnowledgeEngine
from memory import MemoryEngine, MemoryRecord, MemoryStatus
from planning import Goal, Planner, PlannerRules
from reasoning import (
    CarryAwayRule,
    NearbyRelationshipRule,
    ObjectPermanenceRule,
    OcclusionRule,
    ReasoningEngine,
    RecentlyMovedRule,
    RuleRegistry,
    StationaryObjectRule,
)
from scene import SceneGraph, SceneGraphBuilder
from storage import PersistenceStore, PersistentMemory
from storage.memory_quality import compact_persistent_memory
from timeline import Timeline
from tracking import Track, Tracker
from vision import (
    ConfidenceFilter,
    DetectionAdapter,
    DetectionStabilizer,
    Renderer,
    StabilizationPolicy,
    VisionDetector,
)
from world import WorldState

from .pipeline_result import PipelineResult

ZERO_FPS = 0.0
RECENT_PERSISTENT_EVENT_LIMIT = 10


@dataclass(frozen=True)
class PersistentObjectSummary:
    """Human-readable category summary for persistent memory display."""

    category: str
    observations: int
    track_identities_observed: int
    last_seen: datetime
    last_position: tuple[int, int] | None
    currently_observed: bool
    last_known_state: str


class PerceptionPipeline:
    """Own and orchestrate the perception subsystems."""

    def __init__(
        self,
        manager: CameraManager | None = None,
        detector: VisionDetector | None = None,
        adapter: DetectionAdapter | None = None,
        stabilization_policy: StabilizationPolicy | None = None,
        confidence_filter: ConfidenceFilter | None = None,
        detection_stabilizer: DetectionStabilizer | None = None,
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
        planner: Planner | None = None,
        assistant: Assistant | None = None,
        query_engine: QueryEngine | None = None,
        persistence_store: PersistenceStore | None = None,
    ) -> None:
        self.camera_manager = manager or CameraManager()
        self.vision_detector = detector or VisionDetector()
        self.detection_adapter = adapter or DetectionAdapter()
        policy = stabilization_policy or StabilizationPolicy()
        self.confidence_filter = confidence_filter or ConfidenceFilter(
            policy.confidence_threshold
        )
        self.detection_stabilizer = detection_stabilizer or DetectionStabilizer(
            policy
        )
        self.renderer = renderer or Renderer()
        self.tracker = tracker or Tracker()
        self.world_state = world_state or WorldState()
        self.event_engine = event_engine or EventEngine()
        self.event_filter = event_filter or EventFilter()
        self.memory_engine = memory_engine or MemoryEngine()
        self.timeline = timeline or Timeline()
        self.persistence_store = persistence_store or PersistenceStore()
        self._movement_noise_suppressed = 0
        self._visible_track_ids: set[int] = set()
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
        self.planner = planner or Planner(
            self.knowledge_engine,
            self.reasoning_engine,
            PlannerRules(),
        )
        self.assistant = assistant or Assistant(
            self.knowledge_engine,
            self.reasoning_engine,
            self.planner,
        )
        self.query_engine = query_engine or QueryEngine()
        self._frame_durations: deque[float] = deque(maxlen=30)
        self._restore_persistent_memory()

    def start(self) -> None:
        """Start resources required by the pipeline."""
        self.camera_manager.start()

    def process_next_frame(self) -> PipelineResult:
        """Run and return one complete perception cycle."""
        iteration_started = perf_counter()
        frame = self.camera_manager.read_frame()
        raw_results = self.vision_detector.detect(frame)
        detections = self.detection_adapter.convert(raw_results, frame.timestamp)
        detections = self.confidence_filter.filter(detections)
        tracks = self.tracker.update(detections)
        tracks = self.detection_stabilizer.stabilize(tracks)
        identities = self.identity_resolver.update(tracks)
        beliefs = self.belief_engine.update(identities)
        self._apply_beliefs(tracks, beliefs)
        snapshot = self.world_state.update(tracks, frame.timestamp)
        self.scene_graph = self.scene_graph_builder.build(tracks)
        self.knowledge_engine.use_scene_graph(self.scene_graph)
        visible_track_ids = {track.track_id for track in tracks}
        self._visible_track_ids = visible_track_ids
        self.knowledge_engine.use_visible_track_ids(visible_track_ids)
        generated_events = self.event_engine.generate_events(
            self.world_state.previous_snapshot,
            snapshot,
        )
        events = self.event_filter.filter_events(generated_events)
        self.memory_engine.process(events)
        self.timeline.process(events)
        self._update_memory_confidence(tracks)
        if events:
            self._save_persistent_memory()
        observe = getattr(self.reasoning_engine, "observe", None)
        if callable(observe):
            observe([
                record.object_name
                for record in self.memory_engine.store.list_all()
                if record.track_id in visible_track_ids
            ])
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

    def _calculate_fps(self, iteration_started: float) -> float:
        elapsed_seconds = perf_counter() - iteration_started
        if elapsed_seconds <= 0.0:
            return ZERO_FPS
        self._frame_durations.append(elapsed_seconds)
        average_duration = sum(self._frame_durations) / len(self._frame_durations)
        return 1.0 / average_duration if average_duration > 0.0 else ZERO_FPS

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
        if getattr(self.renderer, "plan_requested", False):
            self._print_plan()
        if getattr(self.renderer, "assistant_requested", False):
            self._ask_assistant()
        if getattr(self.renderer, "stabilizer_requested", False):
            self.detection_stabilizer.print_debug()
        if getattr(self.renderer, "persistent_memory_requested", False):
            self._print_persistent_memory()

    def _ask_assistant(self) -> None:
        print("\n========== ASK AETHER ==========")
        print("Type your question in the terminal:")
        try:
            query = input("Question: ")
        except EOFError:
            print("================================")
            return
        if not query.strip():
            print("================================")
            return
        response = self.query_engine.answer(
            query,
            self._current_visible_tracks(),
            self.memory_engine,
            self.timeline,
        )
        print("\nAether:")
        print(response.answer)
        print("================================")

    def _current_visible_tracks(self) -> list[Track]:
        return [
            track
            for track in self.tracker.get_active_tracks()
            if track.track_id in self._visible_track_ids
        ]

    @staticmethod
    def _default_rule_registry() -> RuleRegistry:
        registry = RuleRegistry()
        registry.register(StationaryObjectRule())
        registry.register(NearbyRelationshipRule())
        registry.register(RecentlyMovedRule())
        registry.register(OcclusionRule())
        registry.register(CarryAwayRule())
        registry.register(ObjectPermanenceRule())
        return registry

    def _print_reasoning(self) -> None:
        print("========== Reasoning ==========")
        records = self.memory_engine.store.list_all()
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
            print("\nSupporting Facts")
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

    def _print_plan(self) -> None:
        print("========== Plan ==========")
        goal = self._default_goal()
        if goal is None:
            print("(empty)")
            print("==========================")
            return
        plan = self.planner.create_plan(goal)
        print("\nGoal\n")
        print(f"{goal.goal_type.title()} {self._display_object_name(goal.target_object)}")
        print(f"Priority\n\n{goal.priority}")
        print("\nPlan")
        if not plan.actions:
            print("\n(none)")
        for index, action in enumerate(plan.actions, start=1):
            print(f"\n{index}.\n")
            print(action.description)
            print("\nReason\n")
            print(action.reason)
            print("\nPriority\n")
            print(action.priority)
        print("\nConfidence\n")
        print(f"{plan.confidence:.2f}")
        print("\n==========================")

    def _default_goal(self) -> Goal | None:
        records = self.memory_engine.store.list_all()
        if not records:
            return None
        target = next(
            (record for record in records if record.status.value == "LOST"),
            records[0],
        )
        return Goal(
            goal_type="find",
            target_object=target.object_name,
            priority=1,
            timestamp=datetime.now(),
        )

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

    def _restore_persistent_memory(self) -> None:
        try:
            persistent_memory = self.persistence_store.load()
        except Exception as exc:  # noqa: BLE001 - persistence must not stop startup.
            print(f"Warning: could not load persistent memory: {exc}")
            return
        for record in persistent_memory.objects:
            self.memory_engine.store.add(record)
        for entry in persistent_memory.timeline_entries:
            try:
                self.timeline.store.append(entry)
            except Exception as exc:  # noqa: BLE001 - persistence must not stop startup.
                print(f"Warning: skipped persistent timeline entry: {exc}")
        self._movement_noise_suppressed = persistent_memory.movement_noise_suppressed
        replace_all = getattr(self.belief_engine, "replace_all", None)
        if callable(replace_all):
            replace_all(persistent_memory.beliefs)

    def _save_persistent_memory(self) -> None:
        try:
            self.persistence_store.save(self._persistent_snapshot())
        except Exception as exc:  # noqa: BLE001 - persistence must not stop the loop.
            print(f"Warning: could not save persistent memory: {exc}")

    def _persistent_snapshot(self) -> PersistentMemory:
        return PersistentMemory(
            objects=self.memory_engine.store.list_all(),
            timeline_entries=self.timeline.store.all_entries(),
            beliefs=self.belief_engine.all(),
            movement_noise_suppressed=self._movement_noise_suppressed,
        )

    def _update_memory_confidence(self, tracks: list[Track]) -> None:
        for track in tracks:
            record = self.memory_engine.store.get_by_track_id(track.track_id)
            if record is None:
                continue
            confidence = (
                track.identity_confidence
                if track.identity_confidence is not None
                else track.current_detection.confidence
            )
            record.confidence = confidence
            record.restored = False
            self.memory_engine.store.update(record)

    def _print_persistent_memory(self) -> None:
        print("========== AETHER MEMORY ==========")
        memory = compact_persistent_memory(self._persistent_snapshot())
        summaries = self._persistent_object_summaries(memory.objects)
        entries = memory.timeline_entries
        print("\nOBJECTS")
        if not summaries:
            print("(empty)")
        for summary in summaries:
            current_status = (
                "Currently observed" if summary.currently_observed else "Not observed"
            )
            print(f"\n{self._display_category_name(summary.category)}")
            print(f"  Observations: {summary.observations}")
            print(
                "  Track identities observed: "
                f"{summary.track_identities_observed}"
            )
            print(f"  Last Seen: {summary.last_seen.strftime('%H:%M:%S')}")
            print(f"  Last Position: {summary.last_position}")
            print(f"  Current Status: {current_status}")
            print(f"  Last Known State: {summary.last_known_state}")
        print("\nRECENT EVENTS")
        if not entries:
            print("(empty)")
        for entry in entries[-RECENT_PERSISTENT_EVENT_LIMIT:]:
            category = self._object_category(entry.object_name)
            print(
                f"- {entry.timestamp.strftime('%H:%M:%S')} - "
                f"{self._display_category_name(category)} "
                f"{entry.event_type.value}"
            )
        print("\nMOVEMENT STATISTICS")
        print(f"Movement Events Suppressed: {memory.movement_noise_suppressed}")
        print("\nMEMORY SOURCE")
        print(self._memory_source(memory.objects))
        print("\n====================================")

    def _persistent_object_summaries(
        self,
        records: list[MemoryRecord],
    ) -> list[PersistentObjectSummary]:
        groups: dict[str, list[MemoryRecord]] = {}
        for record in records:
            groups.setdefault(self._object_category(record.object_name), []).append(
                record
            )
        summaries = [
            self._persistent_object_summary(category, group)
            for category, group in groups.items()
        ]
        return sorted(summaries, key=lambda item: item.last_seen, reverse=True)

    def _persistent_object_summary(
        self,
        category: str,
        records: list[MemoryRecord],
    ) -> PersistentObjectSummary:
        latest = max(records, key=lambda item: item.last_seen)
        visible_records = [
            record
            for record in records
            if record.track_id in self._visible_track_ids
            and record.status is not MemoryStatus.LOST
        ]
        track_ids = {record.track_id for record in records}
        return PersistentObjectSummary(
            category=category,
            observations=len(records),
            track_identities_observed=len(track_ids),
            last_seen=latest.last_seen,
            last_position=latest.last_position,
            currently_observed=bool(visible_records),
            last_known_state=self._display_memory_state(latest.status),
        )

    @staticmethod
    def _display_memory_state(status: MemoryStatus) -> str:
        if status is MemoryStatus.MOVING:
            return "Moving"
        if status is MemoryStatus.LOST:
            return "Lost"
        return "Static"

    @staticmethod
    def _memory_source(records: list[MemoryRecord]) -> str:
        has_previous = any(record.restored for record in records)
        has_current = any(not record.restored for record in records)
        if has_current and has_previous:
            return "Current + Previous Sessions"
        if has_previous:
            return "Previous Sessions"
        return "Current Session"

    @staticmethod
    def _object_category(object_name: str) -> str:
        label, separator, suffix = object_name.rpartition("_")
        if separator and suffix.isdigit():
            return label
        return object_name

    @staticmethod
    def _display_category_name(category: str) -> str:
        return category.title()
