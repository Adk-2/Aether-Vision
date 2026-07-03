"""Geometry-only relation types supported by the scene graph."""

from enum import Enum


class RelationType(Enum):
    """Describe a spatial relationship between two tracked objects."""

    LEFT_OF = "LEFT_OF"
    RIGHT_OF = "RIGHT_OF"
    ABOVE = "ABOVE"
    BELOW = "BELOW"
    NEAR = "NEAR"
    OVERLAPS = "OVERLAPS"
