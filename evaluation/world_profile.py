"""Isolated synthetic history-copy profile to explain real-video stage growth."""

from cProfile import Profile
from dataclasses import replace
from datetime import timedelta
from pstats import Stats
from statistics import median
from time import perf_counter
import io
from evaluation.scenarios.common import track, BASE_TIME
from world import WorldState


def run():
    lines = [
        "SYNTHETIC isolation: one fixed track, unique immutable detections; 30 measured snapshots after 5 warm-up updates.",
        "| History entries | p50 update ms |",
        "| ---: | ---: |",
    ]
    for count in (200, 2000):
        item = track("cup")
        item.history = [
            replace(
                item.current_detection,
                detection_id=f"sample-{i}",
                timestamp=BASE_TIME + timedelta(milliseconds=i),
            )
            for i in range(count)
        ]
        item.current_detection = item.history[-1]
        item.last_seen = item.current_detection.timestamp
        world = WorldState()
        samples = []
        for i in range(35):
            started = perf_counter()
            world.update([item], item.last_seen)
            if i >= 5:
                samples.append((perf_counter() - started) * 1000)
        lines.append(f"| {count} | {median(samples):.4f} |")
        if count == 2000:
            profile = Profile()
            profile.runcall(world.update, [item], item.last_seen)
            stream = io.StringIO()
            Stats(profile, stream=stream).sort_stats("cumulative").print_stats(12)
            lines.extend(
                [
                    "",
                    "cProfile for one 2000-entry snapshot (not used in latency medians):",
                    stream.getvalue(),
                ]
            )
    return "\n".join(lines)


if __name__ == "__main__":
    print(run())
