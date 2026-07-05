"""Persistent belief state for a tracked object."""

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class BeliefState:
    """Represent the stable belief associated with one track."""

    track_id: int
    current_belief: str
    confidence: float
    stable_since: datetime
    frames_stable: int
    alternative_beliefs: dict[str, float] = field(default_factory=dict)
