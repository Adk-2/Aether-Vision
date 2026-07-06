"""Supported structured knowledge queries."""

from enum import Enum


class QueryType(Enum):
    """Identify a query supported by the knowledge layer."""

    WHERE_IS = "WHERE_IS"
    WHAT_HAPPENED = "WHAT_HAPPENED"
    OBJECTS_NEAR = "OBJECTS_NEAR"
    CURRENT_BELIEF = "CURRENT_BELIEF"
    CURRENT_STATE = "CURRENT_STATE"
