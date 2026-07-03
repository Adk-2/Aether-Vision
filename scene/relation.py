"""Immutable scene relation representation."""

from dataclasses import dataclass
from datetime import datetime

from .relation_types import RelationType


@dataclass(frozen=True)
class Relation:
    """Represent one directed spatial relationship."""

    subject_track_id: int
    object_track_id: int
    subject_name: str
    object_name: str
    relation_type: RelationType
    timestamp: datetime
