"""Goal model for deterministic planning."""

from dataclasses import dataclass
from datetime import datetime

from .exceptions import PlanningError


@dataclass(frozen=True)
class Goal:
    """Describe what the planner should produce actions for."""

    goal_type: str
    target_object: str
    priority: int
    timestamp: datetime

    def __post_init__(self) -> None:
        if not self.target_object.strip():
            raise PlanningError("Goal target must not be empty or whitespace-only")
