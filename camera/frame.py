"""Canonical image representation used inside Project Aether."""

from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class Frame:
    """Represent one image captured from a camera source."""

    frame_id: int
    image: Any
    timestamp: datetime
    width: int
    height: int
    channels: int
