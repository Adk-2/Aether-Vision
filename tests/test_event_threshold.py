from dataclasses import replace
import pytest
from events import EventEngine, EventType
from events.event_policy import EventPolicy
from events.exceptions import EventError
from evaluation.scenarios.common import track, BASE_TIME
from evaluation.scenarios.event_quality import EventFrame, evaluate
from world import WorldSnapshot


def move(dx, dy, policy, box=(0, 0, 30, 40)):
    engine = EventEngine(policy=policy)
    first = track("cup", center=(0, 0))
    second = track("cup", center=(dx, dy))
    second.current_detection = replace(second.current_detection, bounding_box=box)
    a = WorldSnapshot(BASE_TIME, (first,), 1)
    b = WorldSnapshot(BASE_TIME, (second,), 1)
    engine.generate_events(None, a)
    return engine.generate_events(a, b)


def test_threshold_is_strict_euclidean_and_uses_box_diagonal():
    assert move(1, 0, EventPolicy()) == []
    assert move(1, 1, EventPolicy())[0].event_type is EventType.MOVED
    assert move(3, 4, EventPolicy(min_pixels=1, fraction=0.1)) == []
    assert (
        move(6, 0, EventPolicy(min_pixels=1, fraction=0.1))[0].event_type
        is EventType.MOVED
    )
    assert move(6, 0, EventPolicy(min_pixels=7, fraction=0.1)) == []


@pytest.mark.parametrize("value", [-1, float("nan"), float("inf")])
@pytest.mark.parametrize("field", ["min_pixels", "fraction"])
def test_invalid_thresholds(value, field):
    with pytest.raises(EventError):
        EventPolicy(**{field: value})


def test_no_fixture_events_missed_and_jitter_removed():
    for pipeline in (False, True):
        result = evaluate(pipeline=pipeline)
        assert result.score.value == 1
        metrics = {m.label: m for m in result.metrics}
        assert metrics["jitter false-movement rate"].numerator == 0
        assert metrics["real moves missed"].value == 0


def test_jitter_is_per_track_frame_not_other_tracks_events():
    frames = [
        EventFrame(
            [
                track("cup", track_id=1, center=(0, 0)),
                track("book", track_id=2, center=(0, 0)),
            ],
            ((1, EventType.APPEARED), (2, EventType.APPEARED)),
        ),
        EventFrame(
            [
                track("cup", track_id=1, center=(1, 0)),
                track("book", track_id=2, center=(10, 0)),
            ],
            ((2, EventType.MOVED),),
            (1,),
        ),
    ]
    metrics = {m.label: m for m in evaluate(frames).metrics}
    assert metrics["jitter false-movement rate"].numerator == 0
    assert metrics["jitter false-movement rate"].denominator == 1
    # Two annotated tracks in the same frame are two opportunities, not one.
    frames[1] = replace(frames[1], jitter_tracks=(1, 2))
    metrics = {m.label: m for m in evaluate(frames).metrics}
    assert metrics["jitter false-movement rate"].numerator == 1
    assert metrics["jitter false-movement rate"].denominator == 2


def test_real_move_metric_changes_with_corrupted_truth():
    from evaluation.scenarios.event_quality import pipeline_frames

    frames = pipeline_frames()
    baseline = evaluate(frames, pipeline=True)
    frames[2] = replace(frames[2], expected_events=((1, EventType.STARTED_MOVING),))
    changed = evaluate(frames, pipeline=True)
    assert (
        next(m.value for m in baseline.metrics if m.label == "real moves missed") == 0
    )
    assert next(m.value for m in changed.metrics if m.label == "real moves missed") == 1
