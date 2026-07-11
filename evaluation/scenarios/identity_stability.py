"""Placeholder benchmark for identity stability."""

from evaluation.benchmark import Benchmark
from evaluation.metrics import Score


def run() -> Benchmark:
    """Return a deterministic placeholder identity stability benchmark."""
    return Benchmark(
        name="Identity Stability",
        description="Measures whether object identities remain stable over time.",
        expected_result="Stable identity labels across repeated observations.",
        actual_result="Placeholder: identity labels considered stable.",
        score=Score(0.90),
    )
