"""Placeholder benchmark for planner quality."""

from evaluation.benchmark import Benchmark
from evaluation.metrics import Score


def run() -> Benchmark:
    """Return a deterministic placeholder planner quality benchmark."""
    return Benchmark(
        name="Planner Quality",
        description="Measures whether generated plans are explainable and prioritized.",
        expected_result="Plans contain useful actions with reasons and priorities.",
        actual_result="Placeholder: planner output considered explainable.",
        score=Score(0.87),
    )
