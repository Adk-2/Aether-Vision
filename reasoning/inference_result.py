"""Explainable result of one deterministic inference rule."""

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class InferenceResult:
    """Represent one conclusion and the facts that support it."""

    success: bool
    conclusion: str
    confidence: float
    supporting_facts: list[str] = field(default_factory=list)
    triggered_rules: list[str] = field(default_factory=list)
    timestamp: datetime | None = None
