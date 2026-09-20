"""Shared deterministic fixtures for evaluation scenarios."""

from dataclasses import dataclass
from datetime import datetime, timedelta
import random

from events import Event, EventType
from memory import MemoryEngine, MemoryRecord, MemoryStatus
from scene import Relation, RelationType, SceneGraph
from timeline import Timeline
from tracking import Track
from vision import Detection


BASE_TIME = datetime(2026, 8, 26, 7, 43, 10)


@dataclass(frozen=True)
class LabelFrame:
    """One scripted label observation for a persistent track."""

    label: str
    confidence: float
    expected_label: str


@dataclass(frozen=True)
class LabelObservation:
    """One noisy label observation for a persistent track."""

    track_id: int
    label: str
    confidence: float
    expected_label: str
    center: tuple[int, int]


@dataclass(frozen=True)
class MultiTrackFrame:
    """One scripted frame containing multiple label observations."""

    observations: tuple[LabelObservation, ...]


def flicker_stream() -> list[LabelFrame]:
    """Return a deterministic label-flicker stream with known ground truth."""
    labels = [
        "cup",
        "cup",
        "cup",
        "bottle",
        "cup",
        "cup",
        "cup",
        "bottle",
        "cup",
        "cup",
        "cup",
        "cup",
        "bottle",
        "cup",
        "cup",
        "cup",
        "cup",
        "bottle",
        "cup",
        "cup",
    ]
    return [
        LabelFrame(label=label, confidence=0.92, expected_label="cup")
        for label in labels
    ]


def noisy_multitrack_stream(seed: int = 20260920, frames: int = 240) -> list[MultiTrackFrame]:
    """Return a seeded multi-track stream with noisy labels and confidence bursts."""
    rng = random.Random(seed)
    specs = [
        (1, "cup", ("bottle", "book"), (100, 200)),
        (2, "cell phone", ("remote", "keyboard"), (300, 220)),
    ]
    stream: list[MultiTrackFrame] = []
    for frame_index in range(frames):
        observations: list[LabelObservation] = []
        for track_id, truth, noise_labels, center in specs:
            low_confidence_burst = 80 <= frame_index < 92 and track_id == 1
            if low_confidence_burst:
                label = noise_labels[frame_index % len(noise_labels)]
                confidence = 0.20 + (frame_index % 3) * 0.03
            elif rng.random() < 0.18:
                label = rng.choice(noise_labels)
                confidence = 0.35 + rng.random() * 0.30
            else:
                label = truth
                confidence = 0.82 + rng.random() * 0.15
            observations.append(
                LabelObservation(
                    track_id=track_id,
                    label=label,
                    confidence=confidence,
                    expected_label=truth,
                    center=center,
                )
            )
        stream.append(MultiTrackFrame(tuple(observations)))
    return stream


def relabel_stream() -> list[MultiTrackFrame]:
    """Return a scripted real relabel stream for adaptation measurement."""
    stream: list[MultiTrackFrame] = []
    labels = ["cup"] * 15 + ["bottle"] * 15
    for frame_index, label in enumerate(labels):
        stream.append(
            MultiTrackFrame((
                LabelObservation(
                    track_id=1,
                    label=label,
                    confidence=0.95,
                    expected_label=label,
                    center=(100, 200),
                ),
            ))
        )
    return stream


def track(
    label: str,
    track_id: int = 1,
    frame_index: int = 0,
    center: tuple[int, int] = (100, 200),
    confidence: float = 0.91,
    active: bool = True,
) -> Track:
    """Build one active synthetic track."""
    detection = detection_for(label, track_id, frame_index, center, confidence)
    return Track(
        track_id=track_id,
        current_detection=detection,
        history=[detection],
        first_seen=detection.timestamp,
        last_seen=detection.timestamp,
        age=frame_index + 1,
        missed_frames=0,
        active=active,
    )


def detection_for(
    label: str,
    track_id: int,
    frame_index: int,
    center: tuple[int, int],
    confidence: float = 0.91,
) -> Detection:
    """Build one deterministic synthetic detection."""
    return Detection(
        detection_id=f"detection-{track_id}-{frame_index}",
        class_id=track_id,
        class_name=label,
        confidence=confidence,
        bounding_box=(center[0] - 5, center[1] - 5, center[0] + 5, center[1] + 5),
        center=center,
        timestamp=BASE_TIME + timedelta(seconds=frame_index),
    )


def memory_with_records(records: list[MemoryRecord]) -> MemoryEngine:
    """Build memory populated with supplied records."""
    memory = MemoryEngine()
    for record in records:
        memory.store.add(record)
    return memory


def record(
    object_name: str,
    track_id: int,
    status: MemoryStatus,
    position: tuple[int, int] | None = (100, 200),
    seconds: int = 0,
    events: list[Event] | None = None,
) -> MemoryRecord:
    """Build one deterministic memory record."""
    timestamp = BASE_TIME + timedelta(seconds=seconds)
    return MemoryRecord(
        track_id=track_id,
        object_name=object_name,
        first_seen=BASE_TIME,
        last_seen=timestamp,
        last_position=position,
        status=status,
        history=events or [],
        confidence=0.91,
    )


def event(
    event_type: EventType,
    object_name: str,
    track_id: int,
    seconds: int,
    position: tuple[int, int] | None = (100, 200),
) -> Event:
    """Build one deterministic event."""
    return Event(
        event_type=event_type,
        track_id=track_id,
        timestamp=BASE_TIME + timedelta(seconds=seconds),
        description=f"{object_name} {event_type.value}",
        object_name=object_name,
        position=position,
    )


def timeline_with(events: list[Event]) -> Timeline:
    """Build a timeline from deterministic events."""
    timeline = Timeline()
    timeline.process(sorted(events, key=lambda item: item.timestamp))
    return timeline


def scene_with_near(
    subject_track_id: int,
    object_track_id: int,
    subject_name: str,
    object_name: str,
) -> SceneGraph:
    """Build a scene graph with one NEAR relation."""
    return SceneGraph([
        Relation(
            subject_track_id=subject_track_id,
            object_track_id=object_track_id,
            subject_name=subject_name,
            object_name=object_name,
            relation_type=RelationType.NEAR,
            timestamp=BASE_TIME,
        )
    ])


def label_switch_count(labels: list[str]) -> int:
    """Count adjacent label changes."""
    return sum(
        1
        for previous, current in zip(labels, labels[1:], strict=False)
        if previous != current
    )
