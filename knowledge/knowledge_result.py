"""Canonical result returned by knowledge queries."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from .query_types import QueryType


@dataclass
class KnowledgeResult:
    """Represent the outcome and provenance of one knowledge query."""

    success: bool
    query_type: QueryType
    object_name: str
    result: Any
    confidence: float | None
    timestamp: datetime | None
    source_modules: list[str] = field(default_factory=list)
