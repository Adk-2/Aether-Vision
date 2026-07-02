"""Result produced by one complete perception cycle."""

from dataclasses import dataclass

from camera import Frame
from events import Event
from tracking import Track


@dataclass
class PipelineResult:
    """Represent the output of one complete perception cycle."""

    frame: Frame
    tracks: list[Track]
    events: list[Event]
    fps: float
    should_quit: bool
