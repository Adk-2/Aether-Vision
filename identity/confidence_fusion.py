"""Deterministic confidence accumulation."""


class ConfidenceFusion:
    """Fuse observations by adding confidence to the observed label."""

    def fuse(
        self,
        previous_scores: dict[str, float],
        label: str,
        confidence: float,
    ) -> dict[str, float]:
        """Return updated scores without mutating the supplied statistics."""
        updated = dict(previous_scores)
        updated[label] = updated.get(label, 0.0) + confidence
        return updated
