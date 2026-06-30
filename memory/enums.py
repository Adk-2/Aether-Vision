"""Enumerations used by Project Aether's object memory."""

from enum import Enum, auto


class ObjectState(Enum):
    """Describe the current tracking state of a remembered object."""

    UNKNOWN = auto()
    STATIC = auto()
    MOVING = auto()
    LOST = auto()
    OCCLUDED = auto()
