"""Tests for belief lifecycle and persistence sanitation."""

from datetime import datetime
import json
from pathlib import Path
import sys
import tempfile
import unittest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from belief import BeliefEngine, BeliefPolicy, BeliefState, MIN_BELIEF_CONFIDENCE
from identity import Identity, LabelHistory
from storage import PersistenceStore


class BeliefEngineTests(unittest.TestCase):
    def test_decay_does_not_increment_frames_stable(self) -> None:
        state = _belief(confidence=0.9, frames_stable=7)

        BeliefPolicy().decay(state)

        self.assertLess(state.confidence, 0.9)
        self.assertEqual(state.frames_stable, 7)

    def test_unobserved_belief_is_pruned_after_enough_frames(self) -> None:
        engine = BeliefEngine()
        engine.replace_all([_belief(confidence=0.9, frames_stable=1)])

        engine.update([])
        state = engine.get(1)
        self.assertIsNotNone(state)
        self.assertNotIn("cup", state.alternative_beliefs if state else {})

        frames_elapsed = 0
        while engine.get(1) is not None:
            engine.update([])
            frames_elapsed += 1

        self.assertGreater(frames_elapsed, 0)
        self.assertIsNone(engine.get(1))

    def test_continuously_observed_belief_is_not_pruned(self) -> None:
        engine = BeliefEngine()
        engine.update([_identity(confidence=0.9)])
        unobserved_frames_to_prune = _unobserved_frames_to_prune()

        for _ in range(unobserved_frames_to_prune):
            engine.update([_identity(confidence=0.9)])

        state = engine.get(1)
        self.assertIsNotNone(state)
        self.assertEqual(state.current_belief if state else None, "bottle")
        self.assertGreaterEqual(
            state.confidence if state else 0.0,
            MIN_BELIEF_CONFIDENCE,
        )

    def test_legacy_persistence_drops_stale_belief(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "aether_memory.json"
            path.write_text(json.dumps(_legacy_memory()), encoding="utf-8")

            loaded = PersistenceStore(path).load()

            self.assertEqual(loaded.beliefs, [])


def _unobserved_frames_to_prune() -> int:
    engine = BeliefEngine()
    engine.update([_identity(confidence=0.9)])
    frames_elapsed = 0
    while engine.get(1) is not None:
        engine.update([])
        frames_elapsed += 1
    return frames_elapsed


def _identity(confidence: float = 0.9) -> Identity:
    timestamp = datetime(2026, 8, 26, 7, 43, 10)
    history = LabelHistory()
    history.add_observation("bottle", confidence)
    return Identity(
        track_id=1,
        current_label="bottle",
        confidence=confidence,
        history=history,
        last_updated=timestamp,
    )


def _belief(confidence: float, frames_stable: int) -> BeliefState:
    return BeliefState(
        track_id=1,
        current_belief="bottle",
        confidence=confidence,
        stable_since=datetime(2026, 8, 26, 7, 43, 10),
        frames_stable=frames_stable,
        alternative_beliefs={"cup": 0.01, "book": 0.2},
    )


def _legacy_memory() -> dict[str, object]:
    return {
        "schema_version": 1,
        "memory_source": "Previous Sessions",
        "objects": [],
        "timeline": [],
        "beliefs": [
            {
                "track_id": 1,
                "current_belief": "bottle",
                "confidence": 1e-81,
                "stable_since": "2026-08-26T07:43:10",
                "frames_stable": 9180,
                "alternative_beliefs": {"cup": 1e-81},
            }
        ],
        "movement_noise_suppressed": 0,
    }


if __name__ == "__main__":
    unittest.main()
