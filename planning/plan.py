"""Plan model produced by the planner."""

from dataclasses import dataclass, field
from datetime import datetime

from .action import Action
from .goal import Goal


@dataclass(frozen=True)
class Plan:
    """Represent an explainable deterministic plan."""

    goal: Goal
    actions: list[Action] = field(default_factory=list)
    confidence: float = 0.0
    generated_time: datetime | None = None
