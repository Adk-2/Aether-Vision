"""Stage timings for the actual inference path, or explicitly synthetic inputs."""

from __future__ import annotations
import argparse
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
import platform
from time import perf_counter
from assistant import QueryEngine
from belief import BeliefEngine
from camera import Frame
from events import EventEngine, EventFilter
from identity import IdentityResolver
from memory import MemoryEngine
from timeline import Timeline
from tracking import Tracker
from vision import (
    Detection,
    VisionDetector,
    DetectionAdapter,
    ConfidenceFilter,
    DetectionStabilizer,
    DEFAULT_MODEL_PATH,
)
from world import WorldState

DEFAULT_FRAME_COUNT = 120
BASE_TIME = datetime(2026, 8, 26, 7, 43, 10)
WARMUP = 5


@dataclass
class StageTimings:
    samples: dict[str, list[float]] = field(default_factory=dict)

    def add(self, stage, seconds):
        self.samples.setdefault(stage, []).append(seconds)


def run(
    video_path=None, frame_count=DEFAULT_FRAME_COUNT, model_path=DEFAULT_MODEL_PATH
):
    if frame_count <= WARMUP:
        raise ValueError("Need more than five frames for warm-up and measurement")
    frames = (
        _load_video_frames(video_path, frame_count)
        if video_path
        else _synthetic_frames(frame_count)
    )
    if len(frames) <= WARMUP:
        raise ValueError("Video has no frames remaining after five-frame warm-up")
    detector = VisionDetector(model_path) if video_path else None
    adapter, confidence, stabilizer = (
        DetectionAdapter(),
        ConfidenceFilter(),
        DetectionStabilizer(),
    )
    tracker, identity, beliefs = Tracker(), IdentityResolver(), BeliefEngine()
    engine, event_filter, world = EventEngine(), EventFilter(), WorldState()
    memory, timeline, query = MemoryEngine(), Timeline(), QueryEngine()
    timings, durations = StageTimings(), []
    image_size = "n/a"
    for index, frame in enumerate(frames):
        measured = index >= WARMUP

        def timed(name, function, *args):
            start = perf_counter()
            result = function(*args)
            if measured:
                timings.add(name, perf_counter() - start)
            return result

        start = perf_counter()
        if detector:
            raw = timed("detector", detector.detect, frame)
            # Read the effective inference size after predict has initialized its predictor.
            image_size = str(
                detector._model_loader.load(detector._create_yolo_model).predictor.imgsz
            )
        else:
            # Feed scripted model-shaped results through the real adapter too.
            from types import SimpleNamespace

            scripted = _synthetic_detections(index, frame.timestamp)
            raw = [
                SimpleNamespace(
                    names={d.class_id: d.class_name for d in scripted},
                    boxes=[
                        SimpleNamespace(
                            cls=[d.class_id], conf=[d.confidence], xyxy=[d.bounding_box]
                        )
                        for d in scripted
                    ],
                )
            ]
        detections = timed("adapter", adapter.convert, raw, frame.timestamp)
        detections = timed("confidence filter", confidence.filter, detections)
        tracks = timed("tracker", tracker.update, detections)
        tracks = timed("stabilizer", stabilizer.stabilize, tracks)
        identities = timed("identity", identity.update, tracks)
        states = timed("belief", beliefs.update, identities)

        def update_world():
            by_track = {state.track_id: state for state in states}
            for track in tracks:
                state = by_track.get(track.track_id)
                if state is not None:
                    track.stabilized_label = state.current_belief
                    track.identity_confidence = state.confidence
            return world.update(tracks, frame.timestamp)

        snapshot = timed("world + apply beliefs", update_world)
        events = timed(
            "event engine", engine.generate_events, world.previous_snapshot, snapshot
        )
        events = timed("event filter", event_filter.filter_events, events)
        timed("memory", memory.process, events)
        timed("timeline", timeline.process, events)
        timed("query", query.answer, "where is the cup", tracks, memory, timeline)
        if measured:
            durations.append(perf_counter() - start)
    lines = [
        "========== Project Aether Performance ==========",
        f"Frames: {len(frames)}; warm-up discarded: {WARMUP}; measured: {len(durations)}",
        f"Input: {video_path or 'synthetic frames'}",
        f"Platform: {platform.platform()}",
        f"CPU: {platform.processor() or 'unknown'}",
    ]
    if video_path:
        elapsed = sum(durations)
        lines.extend(
            [
                f"Model path: {Path(model_path).resolve()}",
                f"Image size: inference={image_size}; source={frames[0].width}x{frames[0].height}",
                "Timing scope: detect through query; excludes video decoding, rendering and persistence.",
                f"End-to-end mean FPS: {len(durations) / elapsed:.4f}",
                f"FPS excluding detector: {len(durations) / (elapsed - sum(timings.samples['detector'])):.4f}",
            ]
        )
    else:
        lines.append("SYNTHETIC: detector not run, FPS not representative")
    lines.extend(
        ["", "| Stage | p50 latency ms | p95 latency ms |", "| --- | ---: | ---: |"]
    )
    for stage, samples in timings.samples.items():
        lines.append(
            f"| {stage} | {_percentile(samples, 50) * 1000:.4f} | {_percentile(samples, 95) * 1000:.4f} |"
        )
    lines.append("================================================")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--video")
    parser.add_argument("--frames", type=int, default=DEFAULT_FRAME_COUNT)
    parser.add_argument("--model", default=DEFAULT_MODEL_PATH)
    args = parser.parse_args()
    print(run(args.video, args.frames, args.model))


def _synthetic_frames(frame_count: int) -> list[Frame]:
    return [
        Frame(
            frame_id=index,
            image=None,
            timestamp=BASE_TIME + timedelta(milliseconds=33 * index),
            width=640,
            height=480,
            channels=3,
        )
        for index in range(max(frame_count, 0))
    ]


def _load_video_frames(video_path: str, frame_count: int) -> list[Frame]:
    try:
        import cv2
    except ImportError as exc:
        raise RuntimeError("OpenCV is required for --video benchmarking") from exc

    capture = cv2.VideoCapture(video_path)
    if not capture.isOpened():
        capture.release()
        raise ValueError(f"Cannot open video: {video_path}")
    frames: list[Frame] = []
    index = 0
    while index < frame_count:
        ok, image = capture.read()
        if not ok:
            break
        height, width = image.shape[:2]
        channels = image.shape[2] if len(image.shape) == 3 else 1
        frames.append(
            Frame(
                frame_id=index,
                image=image,
                timestamp=BASE_TIME + timedelta(milliseconds=33 * index),
                width=width,
                height=height,
                channels=channels,
            )
        )
        index += 1
    capture.release()
    if not frames:
        raise ValueError(f"Video yielded zero frames: {video_path}")
    return frames


def _synthetic_detections(frame_index: int, timestamp: datetime) -> list[Detection]:
    offset = frame_index % 40
    return [
        _detection("cup", 0, timestamp, (100 + offset, 200)),
        _detection("book", 1, timestamp, (300, 180 + (offset // 4))),
    ]


def _detection(
    label: str,
    class_id: int,
    timestamp: datetime,
    center: tuple[int, int],
) -> Detection:
    x, y = center
    return Detection(
        detection_id=f"{label}-{timestamp.timestamp()}",
        class_id=class_id,
        class_name=label,
        confidence=0.90,
        bounding_box=(x - 5, y - 5, x + 5, y + 5),
        center=center,
        timestamp=timestamp,
    )


def _percentile(values: list[float], percentile: int) -> float:
    if not values:
        raise ValueError("No latency samples")
    ordered = sorted(values)
    rank = (len(ordered) - 1) * (percentile / 100.0)
    lower = int(rank)
    upper = min(lower + 1, len(ordered) - 1)
    fraction = rank - lower
    return ordered[lower] + (ordered[upper] - ordered[lower]) * fraction


if __name__ == "__main__":
    main()
