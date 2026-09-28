"""Reproducible synthetic threshold sweep; no oracle is derived from predictions."""

from math import hypot
from evaluation.scenarios.event_quality import evaluate
from events.event_policy import EventPolicy

CANDIDATES = (
    (0, 0),
    (0.5, 0),
    (1, 0),
    (2, 0),
    (5, 0),
    (10, 0),
    (0, 0.05),
    (0, 0.1),
    (0, 0.5),
    (1, 0.05),
    (1, 0.1),
)


def run():
    lines = [
        "Synthetic sweep: fixture boxes are 10x10 pixels; displacement must be strictly above threshold.",
        "| min_pixels | fraction | effective px | scenario | jitter (track, frame) | precision | recall | real moves missed |",
        "| ---: | ---: | ---: | --- | --- | --- | --- | ---: |",
    ]
    for pixels, fraction in CANDIDATES:
        for pipeline in (False, True):
            result = evaluate(
                pipeline=pipeline,
                policy=EventPolicy(3 if pipeline else 2, pixels, fraction),
            )
            metrics = {m.label: m for m in result.metrics}
            lines.append(
                f"| {pixels:g} | {fraction:g} | {max(pixels, fraction * hypot(10, 10)):.4f} | {'filtered' if pipeline else 'raw'} | "
                + " | ".join(
                    metrics[label].display
                    for label in (
                        "jitter false-movement rate",
                        "precision tp/(tp+fp)",
                        "recall tp/(tp+fn)",
                        "real moves missed",
                    )
                )
                + " |"
            )
    return "\n".join(lines)


if __name__ == "__main__":
    print(run())
