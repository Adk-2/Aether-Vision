"""Recent label observations for tracked detections."""

from collections import deque

from .exceptions import VisionError
from .stabilization_policy import DEFAULT_EMA_ALPHA, DEFAULT_HISTORY_SIZE

Observation = tuple[str, float]


class LabelHistory:
    """Maintain a bounded, smoothed label history for one track."""

    def __init__(
        self,
        max_size: int = DEFAULT_HISTORY_SIZE,
        ema_alpha: float = DEFAULT_EMA_ALPHA,
    ) -> None:
        if max_size < 1:
            raise VisionError("History size must be at least one")
        if not 0.0 < ema_alpha <= 1.0:
            raise VisionError("EMA alpha must be greater than zero and at most one")
        self._observations: deque[Observation] = deque(maxlen=max_size)
        self._ema_scores: dict[str, float] = {}
        self._ema_alpha = ema_alpha

    @property
    def observations(self) -> tuple[Observation, ...]:
        """Return recent observations in arrival order."""
        return tuple(self._observations)

    @property
    def raw_labels(self) -> tuple[str, ...]:
        """Return recent raw labels in arrival order."""
        return tuple(label for label, _ in self._observations)

    def add_observation(self, label: str, confidence: float) -> None:
        """Record one label and update exponential moving averages."""
        if not label or not label.strip():
            raise VisionError("Label cannot be empty")
        if not 0.0 <= confidence <= 1.0:
            raise VisionError("Confidence must be between zero and one")

        labels = set(self._ema_scores)
        labels.add(label)
        for known_label in labels:
            target = confidence if known_label == label else 0.0
            previous = self._ema_scores.get(known_label, 0.0)
            self._ema_scores[known_label] = (
                self._ema_alpha * target
                + (1.0 - self._ema_alpha) * previous
            )
        self._observations.append((label, confidence))

    def label_counts(self) -> dict[str, int]:
        """Return recent majority-vote counts by label."""
        counts: dict[str, int] = {}
        for label, _ in self._observations:
            counts[label] = counts.get(label, 0) + 1
        return counts

    def weighted_confidences(self) -> dict[str, float]:
        """Return recent cumulative confidence by label."""
        scores: dict[str, float] = {}
        for label, confidence in self._observations:
            scores[label] = scores.get(label, 0.0) + confidence
        return scores

    def ema_scores(self) -> dict[str, float]:
        """Return detached EMA scores by label."""
        return dict(self._ema_scores)

    def top_label(self) -> str | None:
        """Return the strongest label using votes, confidence, and EMA."""
        ranked = self.rank_labels()
        return ranked[0][0] if ranked else None

    def rank_labels(self) -> list[tuple[str, float]]:
        """Rank labels by majority vote, weighted confidence, then EMA."""
        counts = self.label_counts()
        weighted = self.weighted_confidences()
        first_seen: dict[str, int] = {}
        for index, (label, _) in enumerate(self._observations):
            first_seen.setdefault(label, index)
        return sorted(
            weighted.items(),
            key=lambda item: (
                -counts[item[0]],
                -item[1],
                -self._ema_scores.get(item[0], 0.0),
                first_seen[item[0]],
            ),
        )

    def normalized_confidence(self, label: str) -> float:
        """Return a bounded smoothed confidence share for a label."""
        total = sum(self._ema_scores.values())
        return self._ema_scores.get(label, 0.0) / total if total else 0.0

    def vote_count(self, label: str) -> int:
        """Return recent vote count for one label."""
        return self.label_counts().get(label, 0)
