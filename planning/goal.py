"""Goal model for deterministic planning."""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class Goal:
    """Describe what the planner should produce actions for."""

    goal_type: str
    target_object: str
    priority: int
    timestamp: datetime
