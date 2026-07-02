"""World-change event interfaces for Project Aether."""

from .event import Event
from .event_types import EventType
from .exceptions import EventError, WorldStateError

__all__ = ["Event", "EventEngine", "EventError", "EventType", "WorldStateError"]


def __getattr__(name: str) -> object:
    """Load the world-dependent engine only when explicitly requested."""
    if name == "EventEngine":
        from .event_engine import EventEngine

        return EventEngine
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
