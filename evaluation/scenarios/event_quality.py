"""Measured benchmark for event generation quality."""

from collections import Counter
from dataclasses import dataclass
from datetime import timedelta

from evaluation.benchmark import Benchmark
from evaluation.metrics import Score
from evaluation.scenarios.common import BASE_TIME, track
from events import EventEngine, EventType
from tracking import Track
from world import WorldSnapshot

EventKey = tuple[int, int, EventType]


@dataclass(frozen=True)
class EventFrame:
    """One scripted world frame and its expected events."""

    tracks: list[Track]
    expected_events: tuple[tuple[int, EventType], ...]


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
        (),
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
    for frame_index, (center_1, center_2) in enumerate(zip(centers_1, centers_2, strict=True)):
        tracks: list[Track] = []
        if center_1 is not None:
            tracks.append(track("cup", track_id=1, frame_index=frame_index, center=center_1))
        if center_2 is not None:
            tracks.append(track("book", track_id=2, frame_index=frame_index, center=center_2))
        frames.append(EventFrame(tracks, expected_by_frame[frame_index]))
    return frames


def evaluate(frames: list[EventFrame] | None = None) -> Benchmark:
    """Run the real event engine and score event multisets."""
    scripted = scripted_frames() if frames is None else frames
    engine = EventEngine(stopped_frame_threshold=2)
    previous: WorldSnapshot | None = None
    predicted: Counter[EventKey] = Counter()
    expected: Counter[EventKey] = Counter()

    for index, frame in enumerate(scripted):
        snapshot = WorldSnapshot(
            timestamp=BASE_TIME + timedelta(seconds=index),
            tracks=tuple(frame.tracks),
            active_track_count=len(frame.tracks),
        )
        for generated in engine.generate_events(previous, snapshot):
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
    precision_score = Score(
        precision,
        true_positive,
        true_positive + false_positive,
        "precision tp/(tp+fp)",
    )
    recall_score = Score(
        recall,
        true_positive,
        true_positive + false_negative,
        "recall tp/(tp+fn)",
    )
    f1_score = Score(
        f1,
        label="F1",
        raw_counts_text=(
            f"tp={true_positive}; fp={false_positive}; fn={false_negative}"
        ),
    )
    return Benchmark(
        name="Event Quality",
        description=(
            "Real EventEngine on >=30 multiset ground-truth events across two "
            "objects, with jitter/no-move frames, reappearance, simultaneous "
            "events, and stop/start cycles."
        ),
        expected_result=f"{sum(expected.values())} ground-truth events.",
        actual_result=(
            f"tp={true_positive}; fp={false_positive}; fn={false_negative}; "
            f"precision={precision:.4f}; recall={recall:.4f}; f1={f1:.4f}."
        ),
        score=f1_score,
        metrics=(precision_score, recall_score, f1_score),
    )


def run() -> Benchmark:
    """Return the measured event quality benchmark."""
    return evaluate()


def _ratio(numerator: float, denominator: float) -> float:
    return numerator / denominator if denominator else 0.0
