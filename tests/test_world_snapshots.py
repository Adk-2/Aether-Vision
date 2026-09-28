"""Detached snapshots preserve complete histories while sharing immutable values safely."""

from dataclasses import replace
import pytest
from evaluation.scenarios.common import track, BASE_TIME
from world import WorldState
from events.exceptions import WorldStateError


def test_snapshot_keeps_full_history_and_detaches_all_mutable_track_state():
    item = track("cup")
    initial = item.current_detection
    item.history = [replace(initial, detection_id=str(i)) for i in range(2000)]
    item.current_detection = item.history[-1]
    item.stabilized_label = "cup"
    world = WorldState()
    snapshot = world.update([item], BASE_TIME)
    frozen = snapshot.tracks[0]
    assert frozen == item and frozen is not item
    assert frozen.history == item.history and frozen.history is not item.history
    replacement = replace(initial, class_name="book", center=(2, 3))
    item.history[-1] = replacement
    item.history.append(replacement)
    item.current_detection = replacement
    item.stabilized_label = "book"
    item.identity_confidence = 0.2
    assert len(frozen.history) == 2000
    assert frozen.history[-1].class_name == "cup"
    assert frozen.current_detection.class_name == "cup"
    assert frozen.stabilized_label == "cup"
    assert frozen.identity_confidence is None
    latest = world.update([item], BASE_TIME)
    assert world.previous_snapshot is snapshot
    assert world.current_snapshot is latest
    frozen.history.clear()
    frozen.active = False
    assert len(item.history) == len(latest.tracks[0].history) == 2001
    assert item.active and latest.tracks[0].active


def test_snapshot_active_filter_and_duplicate_validation_are_preserved():
    world = WorldState()
    snapshot = world.update(
        [track("cup"), track("book", track_id=2, active=False)], BASE_TIME
    )
    assert snapshot.active_track_count == 1
    assert snapshot.tracks[0].track_id == 1
    with pytest.raises(WorldStateError):
        world.update([track("cup"), track("book")], BASE_TIME)
