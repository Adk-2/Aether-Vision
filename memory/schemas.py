"""Data structures used by Project Aether's object memory."""

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class TrackedObject:
    """Represent the canonical memory state of a tracked object.

    The schema contains detector-independent identity, location, motion, timing,
    and state information for use throughout Project Aether.
    """

    object_id: str
    class_name: str
    bounding_box: tuple[int, int, int, int]
    center: tuple[int, int]
    confidence: float
    velocity: tuple[float, float]
    first_seen: datetime
    last_seen: datetime
    state: str
    history: list[tuple[int, int]] = field(default_factory=list)
