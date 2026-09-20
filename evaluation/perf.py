"""Synthetic performance benchmark for Project Aether stages."""

from __future__ import annotations

import argparse
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import platform
from time import perf_counter

from assistant import QueryEngine
from belief import BeliefEngine
from camera import Frame
from events import EventEngine
from identity import IdentityResolver
from memory import MemoryEngine
from timeline import Timeline
from tracking import Tracker
from vision import Detection
from world import WorldSnapshot

MODEL_NAME = "synthetic-scripted-detector"
DEFAULT_FRAME_COUNT = 120
BASE_TIME = datetime(2026, 8, 26, 7, 43, 10)


@dataclass
class StageTimings:
    """Accumulate per-stage latency samples."""

    samples: dict[str, list[float]] = field(default_factory=dict)

    def add(self, stage: str, seconds: float) -> None:
        """Record one latency sample in seconds."""
        self.samples.setdefault(stage, []).append(seconds)


def main() -> None:
    """Run the stage benchmark and print a plain-text report."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--video", type=str, default=None)
    parser.add_argument("--frames", type=int, default=DEFAULT_FRAME_COUNT)
    args = parser.parse_args()
    print(run(video_path=args.video, frame_count=args.frames))


def run(video_path: str | None = None, frame_count: int = DEFAULT_FRAME_COUNT) -> str:
    """Run the benchmark and return its report text."""
    frames = _load_video_frames(video_path, frame_count) if video_path else _synthetic_frames(frame_count)
    timings = StageTimings()
    tracker = Tracker()
    identity = IdentityResolver()
    beliefs = BeliefEngine()
    events = EventEngine()
    query = QueryEngine()
    memory = MemoryEngine()
    timeline = Timeline()
    previous: WorldSnapshot | None = None
    started = perf_counter()

    for index, frame in enumerate(frames):
        stage_started = perf_counter()
        detections = _synthetic_detections(index, frame.timestamp)
        timings.add("detector", perf_counter() - stage_started)

        stage_started = perf_counter()
        tracks = tracker.update(detections)
        timings.add("tracker", perf_counter() - stage_started)

        stage_started = perf_counter()
        identities = identity.update(tracks)
        timings.add("identity", perf_counter() - stage_started)

        stage_started = perf_counter()
        beliefs.update(identities)
        timings.add("belief", perf_counter() - stage_started)

        stage_started = perf_counter()
        snapshot = WorldSnapshot(
            timestamp=frame.timestamp,
            tracks=tuple(tracks),
            active_track_count=len(tracks),
        )
        generated_events = events.generate_events(previous, snapshot)
        previous = snapshot
        timings.add("events", perf_counter() - stage_started)
        memory.process(generated_events)
        timeline.process(generated_events)

        stage_started = perf_counter()
        query.answer("where is the cup", tracks, memory, timeline)
        timings.add("query", perf_counter() - stage_started)

    elapsed = perf_counter() - started
    mean_fps = len(frames) / elapsed if elapsed > 0.0 else 0.0
    return _report(timings, mean_fps, len(frames), video_path)


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


def _report(
    timings: StageTimings,
    mean_fps: float,
    frame_count: int,
    video_path: str | None,
) -> str:
    lines = [
        "========== Project Aether Performance ==========",
        f"Frames: {frame_count}",
        f"Input: {video_path if video_path else 'synthetic frames'}",
        f"Platform: {platform.platform()}",
        f"CPU: {platform.processor() or 'unknown'}",
        f"Model: {MODEL_NAME}",
        f"Mean FPS: {mean_fps:.4f}",
        "",
        "| Stage | p50 latency ms | p95 latency ms |",
        "| --- | ---: | ---: |",
    ]
    for stage in ["detector", "tracker", "identity", "belief", "events", "query"]:
        samples = timings.samples.get(stage, [])
        lines.append(
            f"| {stage} | {_percentile(samples, 50) * 1000.0:.4f} | "
            f"{_percentile(samples, 95) * 1000.0:.4f} |"
        )
    lines.append("================================================")
    return "\n".join(lines)


def _percentile(values: list[float], percentile: int) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    rank = (len(ordered) - 1) * (percentile / 100.0)
    lower = int(rank)
    upper = min(lower + 1, len(ordered) - 1)
    fraction = rank - lower
    return ordered[lower] + (ordered[upper] - ordered[lower]) * fraction


if __name__ == "__main__":
    main()
