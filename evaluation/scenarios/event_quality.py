"""Measured benchmark for event generation quality."""

from collections import Counter
from dataclasses import dataclass
from datetime import timedelta

from evaluation.benchmark import Benchmark
from evaluation.metrics import Measurement, Score
from evaluation.scenarios.common import BASE_TIME, track
from events import EventEngine, EventFilter, EventType
from events.event_policy import EventPolicy
from tracking import Track
from world import WorldSnapshot

EventKey = tuple[int, int, EventType]


@dataclass(frozen=True)
class EventFrame:
    """One scripted world frame and its expected events."""

    tracks: list[Track]
    expected_events: tuple[tuple[int, EventType], ...]
    jitter_tracks: tuple[int, ...] = ()


def scripted_frames() -> list[EventFrame]:
    """Return a deterministic multi-object event sequence."""
    frames: list[EventFrame] = []
    centers_1 = [
        (10, 10),
        (11, 10),
        (10, 10),
        (20, 10),
        (20, 10),
        (20, 10),
        (25, 10),
        (25, 10),
        (25, 10),
        None,
        (30, 10),
        (30, 10),
        (30, 10),
        (31, 10),
        (30, 10),
        (40, 10),
        (40, 10),
        (40, 10),
        None,
        (50, 10),
        (50, 10),
        (50, 10),
        (60, 10),
        (60, 10),
        (60, 10),
        None,
        (70, 10),
        (70, 10),
        (70, 10),
    ]
    centers_2 = [
        None,
        (100, 100),
        (100, 100),
        (110, 100),
        (110, 100),
        (110, 100),
        None,
        (120, 100),
        (121, 100),
        (120, 100),
        (130, 100),
        (130, 100),
        (130, 100),
        None,
        (140, 100),
        (140, 100),
        (150, 100),
        (150, 100),
        (150, 100),
        (151, 100),
        (150, 100),
        (160, 100),
        (160, 100),
        (160, 100),
        None,
        (170, 100),
        (170, 100),
        (180, 100),
        (180, 100),
    ]
    expected_by_frame: list[tuple[tuple[int, EventType], ...]] = [
        ((1, EventType.APPEARED),),
        ((2, EventType.APPEARED),),
        (),
        ((1, EventType.MOVED), (2, EventType.MOVED)),
        (),
        ((1, EventType.STOPPED), (2, EventType.STOPPED)),
        ((1, EventType.MOVED), (2, EventType.DISAPPEARED)),
        ((2, EventType.APPEARED),),
        ((1, EventType.STOPPED),),
        ((1, EventType.DISAPPEARED),),
        ((1, EventType.APPEARED), (2, EventType.MOVED)),
        (),
        ((1, EventType.STOPPED), (2, EventType.STOPPED)),
        ((2, EventType.DISAPPEARED),),
        ((2, EventType.APPEARED),),
        ((1, EventType.MOVED),),
        ((2, EventType.MOVED),),
        ((1, EventType.STOPPED),),
        ((1, EventType.DISAPPEARED), (2, EventType.STOPPED)),
        ((1, EventType.APPEARED),),
        (),
        ((1, EventType.STOPPED), (2, EventType.MOVED)),
        ((1, EventType.MOVED),),
        ((2, EventType.STOPPED),),
        ((1, EventType.STOPPED), (2, EventType.DISAPPEARED)),
        ((1, EventType.DISAPPEARED), (2, EventType.APPEARED)),
        ((1, EventType.APPEARED),),
        ((2, EventType.MOVED),),
        ((1, EventType.STOPPED),),
    ]
    for frame_index, (center_1, center_2) in enumerate(
        zip(centers_1, centers_2, strict=True)
    ):
        tracks: list[Track] = []
        if center_1 is not None:
            tracks.append(
                track("cup", track_id=1, frame_index=frame_index, center=center_1)
            )
        if center_2 is not None:
            tracks.append(
                track("book", track_id=2, frame_index=frame_index, center=center_2)
            )
        frames.append(
            EventFrame(
                tracks,
                expected_by_frame[frame_index],
                (1,)
                if frame_index in {1, 2, 13, 14}
                else (2,)
                if frame_index in {8, 9, 19, 20}
                else (),
            )
        )
    return frames


def evaluate(
    frames: list[EventFrame] | None = None,
    *,
    pipeline: bool = False,
    policy: EventPolicy | None = None,
) -> Benchmark:
    """Run the real event engine and score event multisets."""
    scripted = (
        (pipeline_frames() if pipeline else scripted_frames())
        if frames is None
        else frames
    )
    if not scripted:
        raise ValueError("No event frames")
    engine = EventEngine(
        policy=policy or EventPolicy(stopped_frame_threshold=3 if pipeline else 2)
    )
    event_filter = EventFilter()
    previous: WorldSnapshot | None = None
    predicted: Counter[EventKey] = Counter()
    expected: Counter[EventKey] = Counter()

    for index, frame in enumerate(scripted):
        snapshot = WorldSnapshot(
            timestamp=BASE_TIME + timedelta(seconds=index),
            tracks=tuple(frame.tracks),
            active_track_count=len(frame.tracks),
        )
        generated_events = engine.generate_events(previous, snapshot)
        if pipeline:
            generated_events = event_filter.filter_events(generated_events)
        for generated in generated_events:
            predicted[(index, generated.track_id, generated.event_type)] += 1
        for track_id, event_type in frame.expected_events:
            expected[(index, track_id, event_type)] += 1
        previous = snapshot

    true_positive = sum((predicted & expected).values())
    false_positive = sum((predicted - expected).values())
    false_negative = sum((expected - predicted).values())
    precision = _ratio(true_positive, true_positive + false_positive)
    recall = _ratio(true_positive, true_positive + false_negative)
    f1 = _ratio(2 * precision * recall, precision + recall)
    jitter_indices = {
        (i, t) for i, frame in enumerate(scripted) for t in frame.jitter_tracks
    }
    for i, t in jitter_indices:
        if t not in {track.track_id for track in scripted[i].tracks}:
            raise ValueError("Jitter annotation references an absent track")
    movement = {
        EventType.MOVED,
        EventType.STOPPED,
        EventType.STARTED_MOVING,
        EventType.STOPPED_MOVING,
    }
    jitter_count = sum(
        any(key[:2] == (i, t) and key[2] in movement for key in predicted)
        for i, t in jitter_indices
    )
    jitter = (
        Score(
            jitter_count / len(jitter_indices),
            jitter_count,
            len(jitter_indices),
            "jitter false-movement rate",
        )
        if jitter_indices
        else Measurement("jitter false-movement rate", "n/a", "")
    )
    mismatches = [
        (i, t, e.name, kind)
        for diff, kind in [
            (predicted - expected, "predicted"),
            (expected - predicted, "missed"),
        ]
        for (i, t, e), count in diff.items()
        for _ in range(count)
    ]
    precision_score = (
        Score(
            precision,
            true_positive,
            true_positive + false_positive,
            "precision tp/(tp+fp)",
        )
        if predicted
        else Measurement("precision tp/(tp+fp)", "n/a", "")
    )
    recall_score = (
        Score(
            recall, true_positive, true_positive + false_negative, "recall tp/(tp+fn)"
        )
        if expected
        else Measurement("recall tp/(tp+fn)", "n/a", "")
    )
    f1_score = Score(
        f1,
        label="F1",
        raw_counts_text=(
            f"tp={true_positive}; fp={false_positive}; fn={false_negative}"
        ),
    )
    return Benchmark(
        name="Event Pipeline Quality (engine + filter)"
        if pipeline
        else "Event Quality",
        description=(
            "Default EventEngine then EventFilter, as PerceptionPipeline; hand-authored transitions, jitter, stop/start, disappearance and reappearance."
            if pipeline
            else "Real EventEngine on >=30 multiset ground-truth events across two "
            "objects, with jitter/no-move frames, reappearance, simultaneous "
            "events, and stop/start cycles."
        ),
        expected_result=f"{sum(expected.values())} ground-truth events.",
        actual_result=(
            f"tp={true_positive}; fp={false_positive}; fn={false_negative}; "
            f"precision={precision:.4f}; recall={recall:.4f}; f1={f1:.4f}; mismatches={mismatches}."
        ),
        score=f1_score,
        metrics=(
            precision_score,
            recall_score,
            f1_score,
            jitter,
            Measurement(
                "real moves missed",
                sum(
                    count
                    for (_, _, kind), count in (expected - predicted).items()
                    if kind in {EventType.MOVED, EventType.STARTED_MOVING}
                ),
                "events",
            ),
        ),
    )


def run() -> Benchmark:
    """Return the measured event quality benchmark."""
    return evaluate()


def _ratio(numerator: float, denominator: float) -> float:
    return numerator / denominator if denominator else 0.0


def pipeline_frames() -> list[EventFrame]:
    """Hand-authored spec: ignore 1px jitter, start on displacement, stop after
    three unchanged frames (EventPolicy default), suppress redundant stops.
    EventFilter APPEARED resets movement state; disappearance removes it.
    This oracle never calls either event component.
    """
    centers = [
        (10, 10),
        (11, 10),
        (10, 10),
        (20, 10),
        (20, 10),
        (20, 10),
        (20, 10),
        (20, 10),
        None,
        (30, 10),
        (30, 10),
        (30, 10),
        (30, 10),
        (40, 10),
        (40, 10),
        (40, 10),
        (40, 10),
        None,
    ]
    expected = {
        0: EventType.APPEARED,
        3: EventType.STARTED_MOVING,
        6: EventType.STOPPED_MOVING,
        8: EventType.DISAPPEARED,
        9: EventType.APPEARED,
        13: EventType.STARTED_MOVING,
        16: EventType.STOPPED_MOVING,
        17: EventType.DISAPPEARED,
    }
    return [
        EventFrame(
            [track("cup", frame_index=i, center=center)] if center else [],
            ((1, expected[i]),) if i in expected else (),
            (1,) if i in {1, 2} else (),
        )
        for i, center in enumerate(centers)
    ]


def run_pipeline() -> Benchmark:
    return evaluate(pipeline=True)
