"""Canonical world-change event representation."""

from dataclasses import dataclass
from datetime import datetime

from .event_types import EventType


@dataclass(frozen=True)
class Event:
    """Represent one observed change involving a tracked object."""

    event_type: EventType
    track_id: int
    timestamp: datetime
    description: str
    object_name: str | None = None
    position: tuple[int, int] | None = None
