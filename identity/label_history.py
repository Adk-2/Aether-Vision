"""Historical label observations for one track."""

from .confidence_fusion import ConfidenceFusion
from .exceptions import IdentityError


class LabelHistory:
    """Accumulate labels, confidence scores, and observation counts."""

    def __init__(self, fusion: ConfidenceFusion | None = None) -> None:
        self._fusion = fusion or ConfidenceFusion()
        self._observations: list[tuple[str, float]] = []
        self._scores: dict[str, float] = {}
        self._counts: dict[str, int] = {}

    @property
    def observation_count(self) -> int:
        """Return the total number of observations."""
        return len(self._observations)

    @property
    def observations(self) -> tuple[tuple[str, float], ...]:
        """Return every observation in arrival order."""
        return tuple(self._observations)

    def add_observation(self, label: str, confidence: float) -> None:
        """Record one validated detector observation."""
        if not label or not label.strip():
            raise IdentityError("Label cannot be empty")
        if not 0.0 <= confidence <= 1.0:
            raise IdentityError("Confidence must be between zero and one")
        self._observations.append((label, confidence))
        self._scores = self._fusion.fuse(self._scores, label, confidence)
        self._counts[label] = self._counts.get(label, 0) + 1

    def best_label(self) -> str | None:
        """Return the highest-scoring label, or None when empty."""
        labels = self.top_labels(1)
        return labels[0][0] if labels else None

    def label_scores(self) -> dict[str, float]:
        """Return detached cumulative confidence scores per label."""
        return dict(self._scores)

    def label_counts(self) -> dict[str, int]:
        """Return detached observation counts per label."""
        return dict(self._counts)

    def top_labels(self, limit: int) -> list[tuple[str, float]]:
        """Return labels ordered by score, then count, then first appearance."""
        if limit < 0:
            raise IdentityError("Label limit cannot be negative")
        order = {label: index for index, (label, _) in enumerate(self._observations)}
        ranked = sorted(
            self._scores.items(),
            key=lambda item: (-item[1], -self._counts[item[0]], order[item[0]]),
        )
        return ranked[:limit]

    def normalized_confidence(self, label: str) -> float:
        """Return one label's share of all accumulated confidence."""
        total = sum(self._scores.values())
        return self._scores.get(label, 0.0) / total if total else 0.0
