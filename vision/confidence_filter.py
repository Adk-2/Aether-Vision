"""Confidence-based filtering for canonical detections."""

from .detection import Detection
from .exceptions import VisionError
from .stabilization_policy import DEFAULT_CONFIDENCE_THRESHOLD


class ConfidenceFilter:
    """Drop detections whose confidence is below a configured threshold."""

    def __init__(self, threshold: float = DEFAULT_CONFIDENCE_THRESHOLD) -> None:
        if not 0.0 <= threshold <= 1.0:
            raise VisionError("Confidence threshold must be between zero and one")
        self.threshold = threshold

    def filter(self, detections: list[Detection]) -> list[Detection]:
        """Return detections whose confidence meets the threshold."""
        return [
            detection
            for detection in detections
            if detection.confidence >= self.threshold
        ]
