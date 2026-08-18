"""Tests for persistent episodic memory."""

from contextlib import redirect_stdout
from datetime import datetime, timedelta
import io
from pathlib import Path
import sys
import tempfile
import unittest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from assistant.response_builder import ResponseBuilder
from belief import BeliefEngine
from events import Event, EventType
from knowledge import KnowledgeEngine
from memory import MemoryEngine, MemoryRecord, MemoryStatus
from pipeline import PerceptionPipeline
from scene import SceneGraph
from storage import PersistenceStore, PersistentMemory
from timeline import Timeline


class FailingPersistenceStore:
    def load(self) -> PersistentMemory:
        return PersistentMemory()

    def save(self, memory: PersistentMemory) -> None:
        raise OSError("disk unavailable")


class PersistenceTests(unittest.TestCase):
    def test_save_empty_memory(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "aether_memory.json"

            PersistenceStore(path).save(PersistentMemory())

            self.assertTrue(path.exists())
            self.assertIn('"objects": []', path.read_text(encoding="utf-8"))

    def test_save_object_memory(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "aether_memory.json"
            store = PersistenceStore(path)

            store.save(PersistentMemory(objects=[_record()]))
            loaded = store.load()

            self.assertEqual(len(loaded.objects), 1)
            self.assertEqual(loaded.objects[0].object_name, "bottle")
            self.assertEqual(loaded.objects[0].confidence, 0.91)

    def test_load_saved_memory(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "aether_memory.json"
            store = PersistenceStore(path)
            memory = PersistentMemory(objects=[_record()])

            store.save(memory)
            loaded = store.load()

            self.assertEqual(loaded.objects[0].last_position, (10, 20))
            self.assertTrue(loaded.objects[0].restored)

    def test_save_and_reload_timeline_entries(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "aether_memory.json"
            store = PersistenceStore(path)
            timeline = Timeline()
            timeline.process([_event()])

            store.save(
                PersistentMemory(timeline_entries=timeline.store.all_entries())
            )
            loaded = store.load()

            self.assertEqual(len(loaded.timeline_entries), 1)
            self.assertEqual(loaded.timeline_entries[0].description, "bottle appeared")

    def test_repeated_movement_events_are_debounced_when_persisted(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "aether_memory.json"
            store = PersistenceStore(path)
            events = [
                _event(EventType.APPEARED, seconds=0),
                _event(EventType.STARTED_MOVING, seconds=1),
                _event(EventType.STOPPED_MOVING, seconds=2),
                _event(EventType.STARTED_MOVING, seconds=2),
                _event(EventType.STOPPED_MOVING, seconds=3),
            ]
            timeline = Timeline()
            timeline.process(events)
            record = _record(history=events, status=MemoryStatus.STATIC)

            store.save(
                PersistentMemory(
                    objects=[record],
                    timeline_entries=timeline.store.all_entries(),
                )
            )
            loaded = store.load()

            event_types = [entry.event_type for entry in loaded.timeline_entries]
            self.assertEqual(
                event_types,
                [EventType.APPEARED, EventType.STARTED_MOVING],
            )
            self.assertEqual(loaded.movement_noise_suppressed, 3)

    def test_appearance_and_disappearance_events_remain_persisted(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "aether_memory.json"
            store = PersistenceStore(path)
            events = [
                _event(EventType.APPEARED, seconds=0),
                _event(EventType.DISAPPEARED, seconds=1),
            ]
            timeline = Timeline()
            timeline.process(events)

            store.save(PersistentMemory(timeline_entries=timeline.store.all_entries()))
            loaded = store.load()

            self.assertEqual(
                [entry.event_type for entry in loaded.timeline_entries],
                [EventType.APPEARED, EventType.DISAPPEARED],
            )

    def test_object_memory_deduplicates_same_logical_name(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "aether_memory.json"
            store = PersistenceStore(path)
            older = _record(track_id=1, object_name="bottle", seconds=0)
            newer = _record(track_id=2, object_name="bottle", seconds=5)

            store.save(PersistentMemory(objects=[older, newer]))
            loaded = store.load()

            self.assertEqual(len(loaded.objects), 1)
            self.assertEqual(loaded.objects[0].track_id, 2)

    def test_historical_memory_survives_pipeline_restart(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "aether_memory.json"
            store = PersistenceStore(path)
            store.save(PersistentMemory(objects=[_record()]))

            pipeline = PerceptionPipeline(
                manager=object(),
                detector=object(),
                adapter=object(),
                renderer=object(),
                tracker=object(),
                persistence_store=PersistenceStore(path),
            )

            records = pipeline.memory_engine.store.list_all()
            self.assertEqual(len(records), 1)
            self.assertTrue(records[0].restored)

    def test_missing_persistence_file(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "missing" / "aether_memory.json"

            loaded = PersistenceStore(path).load()

            self.assertEqual(loaded.objects, [])
            self.assertTrue(path.exists())

    def test_malformed_json(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "aether_memory.json"
            path.write_text("{not-json", encoding="utf-8")

            loaded = PersistenceStore(path).load()

            self.assertEqual(loaded.objects, [])
            self.assertEqual(loaded.timeline_entries, [])

    def test_persistence_failure_does_not_crash_pipeline(self) -> None:
        pipeline = PerceptionPipeline(
            manager=object(),
            detector=object(),
            adapter=object(),
            renderer=object(),
            tracker=object(),
            persistence_store=FailingPersistenceStore(),
        )

        pipeline.memory_engine.store.add(_record())
        pipeline._save_persistent_memory()

    def test_persistent_memory_output_is_concise_and_human_readable(self) -> None:
        pipeline = PerceptionPipeline(
            manager=object(),
            detector=object(),
            adapter=object(),
            renderer=object(),
            tracker=object(),
            persistence_store=FailingPersistenceStore(),
        )
        noisy_events = [
            _event(EventType.APPEARED, object_name="cell phone_002", seconds=0),
            _event(EventType.STARTED_MOVING, object_name="cell phone_002", seconds=1),
            _event(EventType.STOPPED_MOVING, object_name="cell phone_002", seconds=2),
            _event(EventType.STARTED_MOVING, object_name="cell phone_002", seconds=2),
            _event(EventType.STOPPED_MOVING, object_name="cell phone_002", seconds=3),
            _event(EventType.DISAPPEARED, object_name="cell phone_002", seconds=4),
        ]
        pipeline.memory_engine.store.add(
            _record(
                object_name="cell phone_002",
                history=noisy_events,
                status=MemoryStatus.LOST,
                seconds=4,
                restored=True,
            )
        )
        pipeline.timeline.process(noisy_events)
        output = io.StringIO()

        with redirect_stdout(output):
            pipeline._print_persistent_memory()

        text = output.getvalue()
        self.assertIn("========== AETHER MEMORY ==========", text)
        self.assertIn("OBJECTS", text)
        self.assertIn("RECENT EVENTS", text)
        self.assertIn("MOVEMENT STATISTICS", text)
        self.assertIn("Movement Events Suppressed:", text)
        self.assertIn("Current Status: Not observed", text)
        self.assertLessEqual(text.count("started moving"), 1)
        self.assertLessEqual(text.count("stopped moving"), 1)

    def test_multiple_track_identities_aggregate_into_one_category(self) -> None:
        pipeline = _pipeline()
        pipeline.memory_engine.store.add(
            _record(track_id=6, object_name="cell phone_006", seconds=1)
        )
        pipeline.memory_engine.store.add(
            _record(track_id=8, object_name="cell phone_008", seconds=2)
        )
        pipeline.memory_engine.store.add(
            _record(track_id=9, object_name="cell phone_009", seconds=3)
        )

        summaries = pipeline._persistent_object_summaries(
            pipeline.memory_engine.store.list_all()
        )

        self.assertEqual(len(summaries), 1)
        self.assertEqual(summaries[0].category, "cell phone")

    def test_aggregation_reports_observation_count_correctly(self) -> None:
        pipeline = _pipeline()
        for track_id in [6, 8, 9, 10]:
            pipeline.memory_engine.store.add(
                _record(
                    track_id=track_id,
                    object_name=f"cell phone_{track_id:03d}",
                    seconds=track_id,
                )
            )

        summary = pipeline._persistent_object_summaries(
            pipeline.memory_engine.store.list_all()
        )[0]

        self.assertEqual(summary.observations, 4)
        self.assertEqual(summary.track_identities_observed, 4)

    def test_aggregation_reports_current_vs_historical_status(self) -> None:
        pipeline = _pipeline()
        pipeline.memory_engine.store.add(
            _record(
                track_id=6,
                object_name="cell phone_006",
                status=MemoryStatus.MOVING,
            )
        )
        pipeline.memory_engine.store.add(
            _record(
                track_id=8,
                object_name="cell phone_008",
                status=MemoryStatus.LOST,
                restored=True,
            )
        )

        historical = pipeline._persistent_object_summaries(
            pipeline.memory_engine.store.list_all()
        )[0]
        pipeline._visible_track_ids = {6}
        current = pipeline._persistent_object_summaries(
            pipeline.memory_engine.store.list_all()
        )[0]

        self.assertFalse(historical.currently_observed)
        self.assertTrue(current.currently_observed)

    def test_last_known_state_is_separate_from_current_status(self) -> None:
        pipeline = _pipeline()
        pipeline.memory_engine.store.add(
            _record(
                track_id=6,
                object_name="cell phone_006",
                status=MemoryStatus.MOVING,
                restored=True,
            )
        )
        output = io.StringIO()

        with redirect_stdout(output):
            pipeline._print_persistent_memory()

        text = output.getvalue()
        self.assertIn("Current Status: Not observed", text)
        self.assertIn("Last Known State: Moving", text)
        self.assertNotIn("Status: MOVING", text)

    def test_h_output_does_not_expose_raw_track_identity_wall(self) -> None:
        pipeline = _pipeline()
        for track_id in range(1, 13):
            name = f"cell phone_{track_id:03d}"
            pipeline.memory_engine.store.add(
                _record(track_id=track_id, object_name=name, seconds=track_id)
            )
            pipeline.timeline.process(
                [_event(object_name=name, track_id=track_id, seconds=track_id)]
            )
        output = io.StringIO()

        with redirect_stdout(output):
            pipeline._print_persistent_memory()

        text = output.getvalue()
        self.assertEqual(text.count("Cell Phone"), 11)
        self.assertNotIn("cell phone_001", text)
        self.assertNotIn("cell phone_012", text)
        self.assertNotIn("Track Identity", text)
        self.assertEqual(text.count("Observations: 12"), 1)

    def test_historical_object_is_distinguished_from_current_object(self) -> None:
        memory_engine = MemoryEngine()
        memory_engine.store.add(_record(restored=True))
        knowledge = KnowledgeEngine(
            memory_engine,
            Timeline(),
            SceneGraph(),
            BeliefEngine(),
        )
        builder = ResponseBuilder()

        historical = builder.where_is(
            knowledge.where_is("bottle"),
            reasoning=[],
            plan=_empty_plan(),
        )
        knowledge.use_visible_track_ids({1})
        current = builder.where_is(
            knowledge.where_is("bottle"),
            reasoning=[],
            plan=_empty_plan(),
        )

        self.assertIn("was last observed", historical)
        self.assertIn("is currently observed", current)


def _event(
    event_type: EventType = EventType.APPEARED,
    object_name: str = "bottle",
    track_id: int = 1,
    seconds: int = 0,
) -> Event:
    timestamp = datetime(2026, 8, 17, 18, 42) + timedelta(seconds=seconds)
    return Event(
        event_type=event_type,
        track_id=track_id,
        timestamp=timestamp,
        description=f"{object_name} {event_type.value}",
        object_name=object_name,
        position=(10, 20),
    )


def _record(
    restored: bool = False,
    track_id: int = 1,
    object_name: str = "bottle",
    history: list[Event] | None = None,
    status: MemoryStatus = MemoryStatus.ACTIVE,
    seconds: int = 0,
) -> MemoryRecord:
    event = _event(object_name=object_name, track_id=track_id, seconds=seconds)
    return MemoryRecord(
        track_id=track_id,
        object_name=object_name,
        first_seen=event.timestamp,
        last_seen=event.timestamp,
        last_position=event.position,
        status=status,
        history=history or [event],
        confidence=0.91,
        restored=restored,
    )


def _pipeline() -> PerceptionPipeline:
    return PerceptionPipeline(
        manager=object(),
        detector=object(),
        adapter=object(),
        renderer=object(),
        tracker=object(),
        persistence_store=FailingPersistenceStore(),
    )


def _empty_plan() -> object:
    class EmptyPlan:
        actions: list[object] = []

    return EmptyPlan()


if __name__ == "__main__":
    unittest.main()
