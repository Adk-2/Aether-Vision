"""Measured belief stability evaluation."""

from evaluation.scenarios.common import (
    noisy_multitrack_stream as noisy_multitrack_stream,
)
from evaluation.scenarios.label_quality import (
    evaluate as _evaluate,
    frames_until_switch,
    SEEDS,
)


def evaluate(frames=None, adaptation_frames=None, seeds=SEEDS):
    return _evaluate(1, frames, adaptation_frames, seeds)


def _frames_until_switch(frames):
    return frames_until_switch(frames, 1)


def run():
    return evaluate()
