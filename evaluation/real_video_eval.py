"""Evaluate the real perception chain against hand-written video labels."""

from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from hashlib import sha256
import json
from math import hypot, isfinite
from pathlib import Path
from time import perf_counter
from typing import Any, Iterable

from assistant.query import QueryInterpreter
from belief import BeliefEngine
from camera import Frame
from events import EventEngine, EventFilter, EventType
from identity import IdentityResolver
from pipeline import PerceptionPipeline
from tracking import Tracker
from tracking.association import DEFAULT_DISTANCE_THRESHOLD
from vision import (
    DEFAULT_MODEL_PATH,
    ConfidenceFilter,
    DetectionAdapter,
    DetectionStabilizer,
    VisionDetector,
)
from world import WorldState

from .label_video import SCHEMA_VERSION
from .perf import WARMUP, _percentile

ALLOWED_EVENTS = {"appeared", "moved", "stopped", "disappeared", "none"}
EVENT_NAMES = {
    EventType.APPEARED: "appeared",
    EventType.MOVED: "moved",
    EventType.STARTED_MOVING: "moved",
    EventType.STOPPED: "stopped",
    EventType.STOPPED_MOVING: "stopped",
    EventType.DISAPPEARED: "disappeared",
}


@dataclass(frozen=True)
class LabelObject:
    tag: str
    class_name: str
    center: tuple[float, float]


@dataclass(frozen=True)
class LabelEvent:
    tag: str
    event: str


@dataclass(frozen=True)
class LabelFrame:
    frame_index: int
    objects: tuple[LabelObject, ...]
    events: tuple[LabelEvent, ...]


@dataclass(frozen=True)
class Labels:
    path: Path
    digest: str
    video_name: str
    frames: dict[int, LabelFrame]


@dataclass(frozen=True)
class Failure:
    severity: int
    clip: str
    frame_index: int
    kind: str
    detail: str


@dataclass
class QualityCounts:
    true_positive: int = 0
    false_positive: int = 0
    false_negative: int = 0

    @property
    def precision(self) -> float | None:
        total = self.true_positive + self.false_positive
        return self.true_positive / total if total else None

    @property
    def recall(self) -> float | None:
        total = self.true_positive + self.false_negative
        return self.true_positive / total if total else None


@dataclass
class PipelineComponents:
    detector: Any
    adapter: Any
    confidence_filter: Any
    tracker: Any
    stabilizer: Any
    identity: Any
    belief: Any
    world: Any
    event_engine: Any
    event_filter: Any


@dataclass
class ClipResult:
    clip: str
    video_path: Path
    labels_path: Path
    labels_digest: str
    frame_count: int
    labeled_frame_count: int
    source_size: str
    model_path: str
    image_size: str
    tolerance_pixels: float
    detection: QualityCounts = field(default_factory=QualityCounts)
    identity_correct: int = 0
    identity_total: int = 0
    track_switches: int = 0
    events: QualityCounts = field(default_factory=QualityCounts)
    stage_samples: dict[str, list[float]] = field(default_factory=dict)
    frame_durations: list[float] = field(default_factory=list)
    failures: list[Failure] = field(default_factory=list)

    @property
    def mean_fps(self) -> float:
        elapsed = sum(self.frame_durations)
        return len(self.frame_durations) / elapsed if elapsed else 0.0

    @property
    def fps_without_detector(self) -> float:
        elapsed = sum(self.frame_durations) - sum(
            self.stage_samples.get("detector", [])
        )
        return len(self.frame_durations) / elapsed if elapsed > 0 else 0.0


def default_components(model_path: str) -> PipelineComponents:
    """Build the same perception stages and defaults used by the pipeline."""
    return PipelineComponents(
        detector=VisionDetector(model_path),
        adapter=DetectionAdapter(),
        confidence_filter=ConfidenceFilter(),
        tracker=Tracker(),
        stabilizer=DetectionStabilizer(),
        identity=IdentityResolver(),
        belief=BeliefEngine(),
        world=WorldState(),
        event_engine=EventEngine(),
        event_filter=EventFilter(),
    )


def load_labels(path: str | Path, video_path: str | Path) -> Labels:
    """Validate completed hand labels before any detector can run."""
    labels_path = Path(path).resolve()
    raw = labels_path.read_bytes()
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid labels JSON: {exc}") from exc
    if payload.get("schema_version") != SCHEMA_VERSION:
        raise ValueError(f"labels.json must use schema_version {SCHEMA_VERSION}")
    if payload.get("annotation_status") != "complete":
        raise ValueError(
            "Ground truth is not complete; set annotation_status to 'complete' "
            "only after hand-labeling every extracted frame"
        )
    video_name = str(payload.get("video", ""))
    if video_name != Path(video_path).name:
        raise ValueError(
            f"Labels name {video_name!r} does not match video {Path(video_path).name!r}"
        )
    raw_frames = payload.get("frames")
    if not isinstance(raw_frames, list) or not raw_frames:
        raise ValueError("Labels must contain at least one labeled frame")

    frames: dict[int, LabelFrame] = {}
    seen_tags: set[str] = set()
    for raw_frame in raw_frames:
        frame = _parse_label_frame(raw_frame)
        if frame.frame_index in frames:
            raise ValueError(f"Duplicate labeled frame: {frame.frame_index}")
        visible_tags = {item.tag for item in frame.objects}
        if not visible_tags.issubset({item.tag for item in frame.events}):
            missing = sorted(visible_tags - {item.tag for item in frame.events})
            raise ValueError(
                f"Frame {frame.frame_index} has no event/none label for tags: {missing}"
            )
        for item in frame.events:
            if item.event == "appeared" and item.tag not in visible_tags:
                raise ValueError(
                    f"Frame {frame.frame_index}: appeared tag {item.tag!r} is not visible"
                )
            if (
                item.event in {"moved", "stopped", "none"}
                and item.tag not in visible_tags
            ):
                raise ValueError(
                    f"Frame {frame.frame_index}: {item.event} tag {item.tag!r} is not visible"
                )
            if item.event == "disappeared" and item.tag not in seen_tags:
                raise ValueError(
                    f"Frame {frame.frame_index}: disappeared tag {item.tag!r} was never visible"
                )
        seen_tags.update(visible_tags)
        frames[frame.frame_index] = frame
    if list(frames) != sorted(frames):
        raise ValueError("Labeled frames must be ordered by increasing frame_index")
    return Labels(
        path=labels_path,
        digest=sha256(raw).hexdigest(),
        video_name=video_name,
        frames=frames,
    )


def _parse_label_frame(raw: object) -> LabelFrame:
    if not isinstance(raw, dict):
        raise ValueError("Each labeled frame must be an object")
    frame_index = raw.get("frame_index")
    if not isinstance(frame_index, int) or frame_index < 0:
        raise ValueError("frame_index must be a nonnegative integer")
    raw_objects = raw.get("visible_objects")
    raw_events = raw.get("events")
    if not isinstance(raw_objects, list) or not isinstance(raw_events, list):
        raise ValueError(
            f"Frame {frame_index}: visible_objects and events must be arrays"
        )
    objects = tuple(_parse_object(item, frame_index) for item in raw_objects)
    tags = [item.tag for item in objects]
    if len(tags) != len(set(tags)):
        raise ValueError(f"Frame {frame_index}: visible object tags must be unique")
    events = tuple(_parse_event(item, frame_index) for item in raw_events)
    positive_events = [
        (item.tag, item.event) for item in events if item.event != "none"
    ]
    if len(positive_events) != len(set(positive_events)):
        raise ValueError(f"Frame {frame_index}: duplicate positive event label")
    for tag in {item.tag for item in events}:
        names = {item.event for item in events if item.tag == tag}
        if "none" in names and len(names) > 1:
            raise ValueError(
                f"Frame {frame_index}: tag {tag!r} mixes none with a positive event"
            )
    return LabelFrame(frame_index, objects, events)


def _parse_object(raw: object, frame_index: int) -> LabelObject:
    if not isinstance(raw, dict):
        raise ValueError(f"Frame {frame_index}: visible object must be an object")
    tag = raw.get("tag")
    class_name = raw.get("class")
    center = raw.get("center")
    if not isinstance(tag, str) or not tag.strip():
        raise ValueError(f"Frame {frame_index}: object tag must be nonempty")
    if not isinstance(class_name, str) or not class_name.strip():
        raise ValueError(f"Frame {frame_index}: object class must be nonempty")
    if (
        not isinstance(center, list)
        or len(center) != 2
        or any(
            not isinstance(value, (int, float)) or not isfinite(value)
            for value in center
        )
    ):
        raise ValueError(f"Frame {frame_index}: center must be two finite numbers")
    return LabelObject(tag.strip(), normalize_class(class_name), (center[0], center[1]))


def _parse_event(raw: object, frame_index: int) -> LabelEvent:
    if not isinstance(raw, dict):
        raise ValueError(f"Frame {frame_index}: event must be an object")
    tag = raw.get("tag")
    event = raw.get("event")
    if not isinstance(tag, str) or not tag.strip():
        raise ValueError(f"Frame {frame_index}: event tag must be nonempty")
    if event not in ALLOWED_EVENTS:
        raise ValueError(
            f"Frame {frame_index}: event must be one of {sorted(ALLOWED_EVENTS)}"
        )
    return LabelEvent(tag.strip(), event)


def normalize_class(value: str) -> str:
    return QueryInterpreter.normalize_object(value)


def nearest_matches(
    expected_centers: list[tuple[float, float]],
    predicted_centers: list[tuple[float, float]],
    tolerance: float,
) -> tuple[list[tuple[int, int, float]], list[int], list[int]]:
    """Greedily select one-to-one nearest pairs, like tracker association."""
    candidates = sorted(
        (
            hypot(expected[0] - predicted[0], expected[1] - predicted[1]),
            expected_index,
            predicted_index,
        )
        for expected_index, expected in enumerate(expected_centers)
        for predicted_index, predicted in enumerate(predicted_centers)
        if hypot(expected[0] - predicted[0], expected[1] - predicted[1]) <= tolerance
    )
    matched_expected: set[int] = set()
    matched_predicted: set[int] = set()
    matches = []
    for distance, expected_index, predicted_index in candidates:
        if expected_index in matched_expected or predicted_index in matched_predicted:
            continue
        matches.append((expected_index, predicted_index, distance))
        matched_expected.add(expected_index)
        matched_predicted.add(predicted_index)
    return (
        matches,
        [i for i in range(len(expected_centers)) if i not in matched_expected],
        [i for i in range(len(predicted_centers)) if i not in matched_predicted],
    )


def iter_video_frames(video_path: str | Path) -> Iterable[Frame]:
    """Decode every source frame with its source-derived timestamp."""
    import cv2

    path = Path(video_path).resolve()
    capture = cv2.VideoCapture(str(path))
    if not capture.isOpened():
        capture.release()
        raise ValueError(f"Cannot open video: {path}")
    fps = float(capture.get(cv2.CAP_PROP_FPS))
    if not isfinite(fps) or fps <= 0:
        capture.release()
        raise ValueError(f"Video has no usable FPS metadata: {path}")
    index = 0
    try:
        while True:
            ok, image = capture.read()
            if not ok:
                break
            height, width = image.shape[:2]
            yield Frame(
                frame_id=index,
                image=image,
                timestamp=datetime(2026, 1, 1) + timedelta(seconds=index / fps),
                width=width,
                height=height,
                channels=image.shape[2] if len(image.shape) == 3 else 1,
            )
            index += 1
    finally:
        capture.release()
    if index == 0:
        raise ValueError(f"Video yielded zero frames: {path}")


def evaluate(
    video: str | Path,
    labels_path: str | Path,
    *,
    model_path: str = DEFAULT_MODEL_PATH,
    tolerance_pixels: float = DEFAULT_DISTANCE_THRESHOLD,
    components: PipelineComponents | None = None,
    frames: Iterable[Frame] | None = None,
) -> ClipResult:
    """Run the real stage chain and compare only against preloaded hand labels."""
    if not isfinite(tolerance_pixels) or tolerance_pixels < 0:
        raise ValueError("Center tolerance must be finite and nonnegative")
    video_path = Path(video).resolve()
    labels = load_labels(labels_path, video_path)
    pipeline = components or default_components(model_path)
    source_frames = frames if frames is not None else iter_video_frames(video_path)
    result = ClipResult(
        clip=video_path.name,
        video_path=video_path,
        labels_path=labels.path,
        labels_digest=labels.digest,
        frame_count=0,
        labeled_frame_count=len(labels.frames),
        source_size="n/a",
        model_path=str(Path(model_path).resolve()),
        image_size="n/a",
        tolerance_pixels=tolerance_pixels,
    )
    tag_to_track: dict[str, int] = {}
    track_to_tag: dict[int, str] = {}
    event_bucket: list[tuple[int, int, str]] = []

    for frame in source_frames:
        frame_index = frame.frame_id
        measured = frame_index >= WARMUP
        frame_started = perf_counter()

        def timed(stage: str, function: Any, *args: Any) -> Any:
            started = perf_counter()
            value = function(*args)
            if measured:
                result.stage_samples.setdefault(stage, []).append(
                    perf_counter() - started
                )
            return value

        raw = timed("detector", pipeline.detector.detect, frame)
        detections = timed("adapter", pipeline.adapter.convert, raw, frame.timestamp)
        detections = timed(
            "confidence filter", pipeline.confidence_filter.filter, detections
        )
        tracks = timed("tracker", pipeline.tracker.update, detections)
        tracks = timed("stabilizer", pipeline.stabilizer.stabilize, tracks)
        identities = timed("identity", pipeline.identity.update, tracks)
        beliefs = timed("belief", pipeline.belief.update, identities)

        def update_world() -> Any:
            PerceptionPipeline._apply_beliefs(tracks, beliefs)
            return pipeline.world.update(tracks, frame.timestamp)

        snapshot = timed("world + apply beliefs", update_world)
        generated = timed(
            "event engine",
            pipeline.event_engine.generate_events,
            pipeline.world.previous_snapshot,
            snapshot,
        )
        filtered = timed("event filter", pipeline.event_filter.filter_events, generated)
        event_bucket.extend(
            (frame_index, event.track_id, EVENT_NAMES[event.event_type])
            for event in filtered
            if event.event_type in EVENT_NAMES
        )
        if measured:
            result.frame_durations.append(perf_counter() - frame_started)
        result.frame_count += 1
        result.source_size = f"{frame.width}x{frame.height}"

        label_frame = labels.frames.get(frame_index)
        if label_frame is not None:
            _score_label_frame(
                result,
                label_frame,
                detections,
                tracks,
                identities,
                event_bucket,
                tag_to_track,
                track_to_tag,
            )
            event_bucket = []

    if result.frame_count <= WARMUP:
        raise ValueError("Video has no frames remaining after five-frame warm-up")
    missing_frames = sorted(set(labels.frames) - set(range(result.frame_count)))
    if missing_frames:
        raise ValueError(
            f"Labels reference frames beyond decoded video: {missing_frames[:10]}"
        )
    loader = getattr(pipeline.detector, "_model_loader", None)
    model = getattr(loader, "_model", None)
    predictor = getattr(model, "predictor", None)
    if predictor is not None:
        result.image_size = str(getattr(predictor, "imgsz", "n/a"))
    return result


def _score_label_frame(
    result: ClipResult,
    label_frame: LabelFrame,
    detections: list[Any],
    tracks: list[Any],
    identities: list[Any],
    event_bucket: list[tuple[int, int, str]],
    tag_to_track: dict[str, int],
    track_to_tag: dict[int, str],
) -> None:
    expected = list(label_frame.objects)
    matches, unmatched_expected, unmatched_predicted = nearest_matches(
        [item.center for item in expected],
        [item.center for item in detections],
        result.tolerance_pixels,
    )
    for expected_index, predicted_index, distance in matches:
        truth = expected[expected_index]
        prediction = detections[predicted_index]
        predicted_class = normalize_class(prediction.class_name)
        if predicted_class == truth.class_name:
            result.detection.true_positive += 1
        else:
            result.detection.false_positive += 1
            result.detection.false_negative += 1
            _failure(
                result,
                4,
                label_frame.frame_index,
                "wrong detection class",
                f"tag {truth.tag}: expected {truth.class_name}, predicted "
                f"{predicted_class} at {distance:.1f}px",
            )
    for expected_index in unmatched_expected:
        truth = expected[expected_index]
        result.detection.false_negative += 1
        _failure(
            result,
            4,
            label_frame.frame_index,
            "missed detection",
            f"tag {truth.tag}: {truth.class_name} at {truth.center}",
        )
    for predicted_index in unmatched_predicted:
        prediction = detections[predicted_index]
        result.detection.false_positive += 1
        _failure(
            result,
            2,
            label_frame.frame_index,
            "extra detection",
            f"predicted {normalize_class(prediction.class_name)} at {prediction.center}",
        )

    observed_tracks = [track for track in tracks if track.missed_frames == 0]
    track_matches, _, _ = nearest_matches(
        [item.center for item in expected],
        [track.current_detection.center for track in observed_tracks],
        result.tolerance_pixels,
    )
    identities_by_track = {item.track_id: item for item in identities}
    for expected_index, track_index, distance in track_matches:
        truth = expected[expected_index]
        track = observed_tracks[track_index]
        prior_track = tag_to_track.get(truth.tag)
        if prior_track is not None and prior_track != track.track_id:
            result.track_switches += 1
            _failure(
                result,
                6,
                label_frame.frame_index,
                "track ID switch",
                f"tag {truth.tag}: track {prior_track} -> {track.track_id}",
            )
        tag_to_track[truth.tag] = track.track_id
        track_to_tag[track.track_id] = truth.tag
        identity = identities_by_track.get(track.track_id)
        result.identity_total += 1
        actual = (
            normalize_class(identity.current_label) if identity is not None else None
        )
        if actual == truth.class_name:
            result.identity_correct += 1
        else:
            _failure(
                result,
                5,
                label_frame.frame_index,
                "identity label mismatch",
                f"tag {truth.tag}, track {track.track_id}: expected "
                f"{truth.class_name}, got {actual or 'missing'} at {distance:.1f}px",
            )

    expected_events = Counter(
        (item.tag, item.event) for item in label_frame.events if item.event != "none"
    )
    predicted_events = Counter(
        (track_to_tag.get(track_id, f"track:{track_id}"), event)
        for _, track_id, event in event_bucket
    )
    result.events.true_positive += sum((expected_events & predicted_events).values())
    false_positive = predicted_events - expected_events
    false_negative = expected_events - predicted_events
    result.events.false_positive += sum(false_positive.values())
    result.events.false_negative += sum(false_negative.values())
    for (tag, event), count in false_positive.items():
        source_frames = [
            source_frame
            for source_frame, track_id, predicted_event in event_bucket
            if track_to_tag.get(track_id, f"track:{track_id}") == tag
            and predicted_event == event
        ]
        for index in range(count):
            source_frame = (
                source_frames[index] if index < len(source_frames) else "unknown"
            )
            _failure(
                result,
                3,
                label_frame.frame_index,
                "extra filtered event",
                f"interval event {event} for {tag}, emitted at frame {source_frame}",
            )
    for (tag, event), count in false_negative.items():
        for _ in range(count):
            _failure(
                result,
                5,
                label_frame.frame_index,
                "missed filtered event",
                f"interval ending here expected {event} for {tag}",
            )


def _failure(
    result: ClipResult,
    severity: int,
    frame_index: int,
    kind: str,
    detail: str,
) -> None:
    result.failures.append(Failure(severity, result.clip, frame_index, kind, detail))


def _percentage(value: float | None) -> str:
    return "n/a" if value is None else f"{value * 100:.2f}%"


def _quality_summary(counts: QualityCounts) -> str:
    return (
        f"precision {_percentage(counts.precision)} "
        f"(tp={counts.true_positive}, fp={counts.false_positive}); "
        f"recall {_percentage(counts.recall)} "
        f"(tp={counts.true_positive}, fn={counts.false_negative})"
    )


def render_report(results: list[ClipResult], notable_limit: int = 10) -> str:
    """Render per-clip and pooled results as one Markdown report."""
    if not results:
        raise ValueError("No real-video results to report")
    lines = [
        "# Aether real-video evaluation",
        "",
        "Ground truth was loaded, validated, and SHA-256 hashed before detector "
        "construction/inference. Event labels close the interval since the previous "
        "labeled frame. Class matching uses normalized names and the existing tracker "
        f"distance threshold ({results[0].tolerance_pixels:g} pixels by default).",
        "",
        "## Clip list",
        "",
        "| Clip | Frames | Labeled frames | Source size | Labels SHA-256 |",
        "| --- | ---: | ---: | --- | --- |",
    ]
    for result in results:
        lines.append(
            f"| {result.clip} | {result.frame_count} | {result.labeled_frame_count} "
            f"| {result.source_size} | `{result.labels_digest}` |"
        )

    lines.extend(["", "## Per-clip quality", ""])
    for result in results:
        identity = (
            f"{_percentage(result.identity_correct / result.identity_total)} "
            f"({result.identity_correct}/{result.identity_total})"
            if result.identity_total
            else "n/a"
        )
        lines.extend(
            [
                f"### {result.clip}",
                "",
                "| Metric | Result |",
                "| --- | --- |",
                f"| Detected objects | {_quality_summary(result.detection)} |",
                f"| Identity label on spatially matched objects | {identity} |",
                f"| Track ID switches | {result.track_switches} |",
                f"| Filtered events | {_quality_summary(result.events)} |",
                "",
                f"Model path: `{result.model_path}`  ",
                f"Inference image size: `{result.image_size}`  ",
                f"End-to-end mean FPS: {result.mean_fps:.4f}  ",
                f"FPS excluding detector: {result.fps_without_detector:.4f}",
                "",
                "| Stage | p50 latency ms | p95 latency ms |",
                "| --- | ---: | ---: |",
            ]
        )
        for stage, samples in result.stage_samples.items():
            lines.append(
                f"| {stage} | {_percentile(samples, 50) * 1000:.4f} | "
                f"{_percentile(samples, 95) * 1000:.4f} |"
            )
        lines.append("")

    pooled_detection = QualityCounts(
        sum(item.detection.true_positive for item in results),
        sum(item.detection.false_positive for item in results),
        sum(item.detection.false_negative for item in results),
    )
    pooled_events = QualityCounts(
        sum(item.events.true_positive for item in results),
        sum(item.events.false_positive for item in results),
        sum(item.events.false_negative for item in results),
    )
    identity_correct = sum(item.identity_correct for item in results)
    identity_total = sum(item.identity_total for item in results)
    pooled_samples: dict[str, list[float]] = {}
    for result in results:
        for stage, samples in result.stage_samples.items():
            pooled_samples.setdefault(stage, []).extend(samples)
    pooled_durations = [value for result in results for value in result.frame_durations]
    detector_seconds = sum(pooled_samples.get("detector", []))
    elapsed = sum(pooled_durations)
    non_detector_elapsed = elapsed - detector_seconds
    pooled_identity = (
        f"{_percentage(identity_correct / identity_total)} "
        f"({identity_correct}/{identity_total})"
        if identity_total
        else "n/a"
    )
    lines.extend(
        [
            "## Pooled",
            "",
            "| Metric | Result |",
            "| --- | --- |",
            f"| Detected objects | {_quality_summary(pooled_detection)} |",
            f"| Identity label on spatially matched objects | {pooled_identity} |",
            f"| Track ID switches | {sum(item.track_switches for item in results)} |",
            f"| Filtered events | {_quality_summary(pooled_events)} |",
            f"| End-to-end mean FPS | "
            f"{len(pooled_durations) / elapsed if elapsed else 0.0:.4f} |",
            f"| FPS excluding detector | "
            f"{len(pooled_durations) / non_detector_elapsed if non_detector_elapsed > 0 else 0.0:.4f} |",
            "",
            "| Stage | p50 latency ms | p95 latency ms |",
            "| --- | ---: | ---: |",
        ]
    )
    for stage, samples in pooled_samples.items():
        lines.append(
            f"| {stage} | {_percentile(samples, 50) * 1000:.4f} | "
            f"{_percentile(samples, 95) * 1000:.4f} |"
        )

    failures = sorted(
        (failure for result in results for failure in result.failures),
        key=lambda item: (-item.severity, item.clip, item.frame_index, item.kind),
    )[:notable_limit]
    lines.extend(["", "## Notable failures", ""])
    if failures:
        lines.extend(
            [
                "| Clip | Frame | Type | Concrete mismatch |",
                "| --- | ---: | --- | --- |",
            ]
        )
        for failure in failures:
            lines.append(
                f"| {failure.clip} | {failure.frame_index} | {failure.kind} | "
                f"{failure.detail} |"
            )
    else:
        lines.append("No mismatches were observed in the labeled frames.")
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--video", required=True)
    parser.add_argument("--labels", required=True)
    parser.add_argument("--model", default=DEFAULT_MODEL_PATH)
    parser.add_argument(
        "--center-tolerance",
        type=float,
        default=DEFAULT_DISTANCE_THRESHOLD,
        help="maximum center distance in pixels; defaults to the tracker threshold",
    )
    parser.add_argument("--output")
    args = parser.parse_args()
    result = evaluate(
        args.video,
        args.labels,
        model_path=args.model,
        tolerance_pixels=args.center_tolerance,
    )
    report = render_report([result])
    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(report, encoding="utf-8")
        print(f"Report: {output.resolve()}")
    else:
        print(report, end="")


if __name__ == "__main__":
    main()
