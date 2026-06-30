"""Persistent object identity representation."""

from dataclasses import dataclass
from datetime import datetime

from vision.detection import Detection


@dataclass
class Track:
    """Represent one persistent object identity across frames."""

    track_id: int
    current_detection: Detection
    history: list[Detection]
    first_seen: datetime
    last_seen: datetime
    age: int
    missed_frames: int
    active: bool
