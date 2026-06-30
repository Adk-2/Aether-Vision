"""Pure-Python distance calculations for object association."""

from math import hypot
from typing import TypeAlias

Center: TypeAlias = tuple[int, int]


def euclidean_distance(first: Center, second: Center) -> float:
    """Return the Euclidean distance between two center coordinates."""
    first_x, first_y = first
    second_x, second_y = second
    return hypot(second_x - first_x, second_y - first_y)
