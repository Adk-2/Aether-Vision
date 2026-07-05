"""Resolved identity representation."""

from dataclasses import dataclass
from datetime import datetime

from .label_history import LabelHistory


@dataclass
class Identity:
    """Represent the current stabilized identity for one track."""

    track_id: int
    current_label: str
    confidence: float
    history: LabelHistory
    last_updated: datetime
