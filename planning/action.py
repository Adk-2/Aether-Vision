"""Action model for deterministic plans."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Action:
    """Represent one recommended action and its explanation."""

    description: str
    priority: int
    reason: str
