"""Immutable representation of one event on the episodic timeline."""

from dataclasses import dataclass
from datetime import datetime

from events import EventType


@dataclass(frozen=True)
class TimelineEntry:
    """Represent one immutable historical event."""

    sequence_number: int
    timestamp: datetime
    track_id: int
    object_name: str
    event_type: EventType
    description: str
