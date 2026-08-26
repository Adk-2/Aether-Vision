"""Explicit response model for deterministic Aether queries."""

from dataclasses import dataclass
from enum import Enum


class QuerySource(Enum):
    """Describe where a deterministic answer came from."""

    CURRENT = "CURRENT"
    MEMORY = "MEMORY"
    TIMELINE = "TIMELINE"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class QueryResponse:
    """Structured answer produced by the query engine."""

    answer: str
    source: QuerySource
