"""Canonical detection representation used by Project Aether."""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class Detection:
    """Represent one object detected in a frame."""

    detection_id: str
    class_id: int
    class_name: str
    confidence: float
    bounding_box: tuple[int, int, int, int]
    center: tuple[int, int]
    timestamp: datetime
