"""Working-memory representation of one tracked object."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from events import Event


class MemoryStatus(Enum):
    """Describe the latest event-derived state of an object."""

    ACTIVE = "ACTIVE"
    MOVING = "MOVING"
    STATIC = "STATIC"
    LOST = "LOST"


@dataclass
class MemoryRecord:
    """Represent the latest known state and event history of one object."""

    track_id: int
    object_name: str
    first_seen: datetime
    last_seen: datetime
    last_position: tuple[int, int] | None
    status: MemoryStatus
    history: list[Event] = field(default_factory=list)
