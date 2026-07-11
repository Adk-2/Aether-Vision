"""Benchmark model for one evaluation scenario."""

from dataclasses import dataclass

from .metrics import Score


@dataclass(frozen=True)
class Benchmark:
    """Represent one repeatable evaluation scenario result."""

    name: str
    description: str
    expected_result: str
    actual_result: str
    score: Score
