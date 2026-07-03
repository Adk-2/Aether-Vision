"""Result produced by one complete perception cycle."""

from dataclasses import dataclass, field

from camera import Frame
from events import Event
from scene import SceneGraph
from tracking import Track


@dataclass
class PipelineResult:
    """Represent the output of one complete perception cycle."""

    frame: Frame
    tracks: list[Track]
    events: list[Event]
    fps: float
    should_quit: bool
    scene_graph: SceneGraph = field(default_factory=SceneGraph)
