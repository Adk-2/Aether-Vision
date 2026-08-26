"""Tests for deterministic natural-language memory queries."""

from datetime import datetime
from pathlib import Path
import sys
import unittest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from assistant import QueryEngine, QuerySource
from events import Event, EventType
from memory import MemoryEngine, MemoryRecord, MemoryStatus
from timeline import Timeline
from tracking import Track
from vision import Detection


class QueryEngineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = QueryEngine()
        self.memory = MemoryEngine()
        self.timeline = Timeline()

    def test_current_object_query(self) -> None:
        response = self.engine.answer(
            "Where is the phone?",
            [_track("cell phone", center=(396, 263))],
            self.memory,
            self.timeline,
        )

        self.assertEqual(response.source, QuerySource.CURRENT)
        self.assertIn("currently visible", response.answer)
        self.assertIn("(396, 263)", response.answer)

    def test_historical_object_query(self) -> None:
        self.memory.store.add(_record("cell phone_003"))

        response = self.engine.answer(
            "Where is the phone?",
            [],
            self.memory,
            self.timeline,
        )

        self.assertEqual(response.source, QuerySource.MEMORY)
        self.assertIn("not currently visible", response.answer)
        self.assertIn("(396, 263)", response.answer)
        self.assertIn("07:43:10", response.answer)

    def test_unknown_object_query(self) -> None:
        response = self.engine.answer(
            "Where is the remote?",
            [],
            self.memory,
            self.timeline,
        )

        self.assertEqual(response.source, QuerySource.UNKNOWN)
        self.assertEqual(
            response.answer,
            "I don't have a reliable observation of a remote.",
        )

    def test_current_object_list(self) -> None:
        self.memory.store.add(_record("cell phone_003"))

        response = self.engine.answer(
            "What objects do you see?",
            [_track("person"), _track("chair")],
            self.memory,
            self.timeline,
        )

        self.assertEqual(response.source, QuerySource.CURRENT)
        self.assertIn("- chair", response.answer)
        self.assertIn("- person", response.answer)
        self.assertNotIn("cell phone", response.answer)

    def test_recent_history_query(self) -> None:
        for index, event_type in enumerate(
            [
                EventType.APPEARED,
                EventType.MOVED,
                EventType.DISAPPEARED,
                EventType.APPEARED,
                EventType.STOPPED,
                EventType.DISAPPEARED,
            ],
            start=1,
        ):
            self.timeline.process([
                _event(f"object_{index:03d}", index, event_type)
            ])

        response = self.engine.answer(
            "What happened recently?",
            [],
            self.memory,
            self.timeline,
        )

        self.assertEqual(response.source, QuerySource.TIMELINE)
        self.assertIn("Recently observed:", response.answer)
        self.assertEqual(response.answer.count("- "), 5)
        self.assertNotIn("object_001", response.answer)

    def test_last_seen_query(self) -> None:
        self.memory.store.add(_record("cell phone_003"))

        response = self.engine.answer(
            "When was the phone last seen?",
            [],
            self.memory,
            self.timeline,
        )

        self.assertIn("07:43:10", response.answer)
        self.assertIn("not currently visible", response.answer)

    def test_visibility_query(self) -> None:
        response = self.engine.answer(
            "Is the phone visible?",
            [_track("cell phone")],
            self.memory,
            self.timeline,
        )

        self.assertEqual(
            response.answer,
            "Yes. The cell phone is currently visible.",
        )

    def test_phone_mobile_alias_normalization(self) -> None:
        response = self.engine.answer(
            "Where is the mobile?",
            [_track("cell phone", center=(12, 34))],
            self.memory,
            self.timeline,
        )

        self.assertIn("cell phone", response.answer)
        self.assertIn("(12, 34)", response.answer)

    def test_multiple_visible_objects(self) -> None:
        response = self.engine.answer(
            "Where is the phone?",
            [
                _track("cell phone", track_id=1, center=(10, 20)),
                _track("cell phone", track_id=2, center=(30, 40)),
            ],
            self.memory,
            self.timeline,
        )

        self.assertIn("There are 2 cell phones currently visible.", response.answer)
        self.assertIn("(10, 20)", response.answer)
        self.assertIn("(30, 40)", response.answer)

    def test_historical_position_is_never_described_as_current(self) -> None:
        self.memory.store.add(_record("cell phone_003"))

        response = self.engine.answer(
            "Where is the phone?",
            [],
            self.memory,
            self.timeline,
        )

        self.assertNotIn("currently visible at", response.answer)
        self.assertIn("was last observed", response.answer)


def _track(
    class_name: str,
    track_id: int = 1,
    center: tuple[int, int] = (100, 200),
) -> Track:
    timestamp = datetime(2026, 8, 26, 7, 43, 10)
    detection = Detection(
        detection_id=f"detection-{track_id}",
        class_id=0,
        class_name=class_name,
        confidence=0.91,
        bounding_box=(0, 0, 10, 10),
        center=center,
        timestamp=timestamp,
    )
    return Track(
        track_id=track_id,
        current_detection=detection,
        history=[detection],
        first_seen=timestamp,
        last_seen=timestamp,
        age=1,
        missed_frames=0,
        active=True,
    )


def _record(object_name: str) -> MemoryRecord:
    timestamp = datetime(2026, 8, 26, 7, 43, 10)
    return MemoryRecord(
        track_id=3,
        object_name=object_name,
        first_seen=timestamp,
        last_seen=timestamp,
        last_position=(396, 263),
        status=MemoryStatus.LOST,
    )


def _event(
    object_name: str,
    track_id: int,
    event_type: EventType,
) -> Event:
    return Event(
        event_type=event_type,
        track_id=track_id,
        timestamp=datetime(2026, 8, 26, 7, 43, track_id),
        description=f"{object_name} {event_type.value}",
        object_name=object_name,
        position=(track_id, track_id),
    )


if __name__ == "__main__":
    unittest.main()
