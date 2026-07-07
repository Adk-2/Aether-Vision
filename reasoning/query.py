"""Lightweight structured reasoning query API."""

from .inference_result import InferenceResult
from .reasoning_engine import ReasoningEngine


class ReasoningQuery:
    """Delegate explicit inference requests to a reasoning engine."""

    def __init__(self, engine: ReasoningEngine) -> None:
        self._engine = engine

    def infer(self, object_name: str) -> list[InferenceResult]:
        return self._engine.infer(object_name)


def infer(
    engine: ReasoningEngine,
    object_name: str,
) -> list[InferenceResult]:
    """Evaluate registered rules for an object."""
    return engine.infer(object_name)
