"""Facts collected for one object before rule evaluation."""

from dataclasses import dataclass, field
from datetime import datetime


@dataclass(frozen=True)
class Inference:
    """Provide rules with a detached, object-specific knowledge view."""

    object_name: str
    current_state: str | None
    location: tuple[int, int] | None
    nearby_objects: list[str] = field(default_factory=list)
    recent_events: list[str] = field(default_factory=list)
    recent_movement: bool = False
    recently_disappeared: bool = False
    removal_evidence: bool = False
    destruction_evidence: bool = False
    nearby_people: list[str] = field(default_factory=list)
    people_recently_moved_away: list[str] = field(default_factory=list)
    inferred_conclusions: list[str] = field(default_factory=list)
    timestamp: datetime | None = None
