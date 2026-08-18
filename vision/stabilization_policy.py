"""Configuration for deterministic detection stabilization."""

from dataclasses import dataclass

from .exceptions import VisionError

DEFAULT_HISTORY_SIZE = 20
DEFAULT_CONFIDENCE_THRESHOLD = 0.35
DEFAULT_MINIMUM_VOTES_BEFORE_LABEL_CHANGE = 2
DEFAULT_EMA_ALPHA = 0.4


@dataclass(frozen=True)
class StabilizationPolicy:
    """Control label history, confidence gating, and smoothing behavior."""

    history_size: int = DEFAULT_HISTORY_SIZE
    confidence_threshold: float = DEFAULT_CONFIDENCE_THRESHOLD
    minimum_votes_before_label_change: int = (
        DEFAULT_MINIMUM_VOTES_BEFORE_LABEL_CHANGE
    )
    ema_alpha: float = DEFAULT_EMA_ALPHA

    def __post_init__(self) -> None:
        if self.history_size < 1:
            raise VisionError("History size must be at least one")
        if not 0.0 <= self.confidence_threshold <= 1.0:
            raise VisionError("Confidence threshold must be between zero and one")
        if self.minimum_votes_before_label_change < 1:
            raise VisionError("Minimum votes before label change must be at least one")
        if not 0.0 < self.ema_alpha <= 1.0:
            raise VisionError("EMA alpha must be greater than zero and at most one")
