"""Repeatable benchmark evaluation framework for Project Aether."""

from .benchmark import Benchmark
from .metrics import Average, Counter, Percentage, Score
from .report import EvaluationReport

__all__ = [
    "Average",
    "Benchmark",
    "Counter",
    "EvaluationReport",
    "Evaluator",
    "Percentage",
    "Score",
]


def __getattr__(name: str) -> object:
    """Lazily expose Evaluator without importing the runner at package load."""
    if name == "Evaluator":
        from .evaluator import Evaluator

        return Evaluator
    raise AttributeError(f"module 'evaluation' has no attribute {name!r}")
