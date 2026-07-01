"""Immutable view of the tracked world at one instant."""

from dataclasses import dataclass
from datetime import datetime

from tracking import Track


@dataclass(frozen=True)
class WorldSnapshot:
    """Represent the complete active world at one timestamp."""

    timestamp: datetime
    tracks: tuple[Track, ...]
    active_track_count: int
