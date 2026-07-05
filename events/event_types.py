"""Types of observable world changes."""

from enum import Enum


class EventType(Enum):
    """Classify changes between consecutive world snapshots."""

    APPEARED = "appeared"
    DISAPPEARED = "disappeared"
    MOVED = "moved"
    STOPPED = "stopped"
    STARTED_MOVING = "started moving"
    STOPPED_MOVING = "stopped moving"
