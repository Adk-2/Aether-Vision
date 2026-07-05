"""Configurable policy for behavioral event filtering."""

from dataclasses import dataclass

from .event_types import EventType
from .exceptions import EventError

DEFAULT_STOPPED_FRAME_THRESHOLD = 3
MINIMUM_STOPPED_FRAME_THRESHOLD = 1


@dataclass(frozen=True)
class EventPolicy:
    """Centralize deterministic event filtering configuration."""

    stopped_frame_threshold: int = DEFAULT_STOPPED_FRAME_THRESHOLD

    def __post_init__(self) -> None:
        if self.stopped_frame_threshold < MINIMUM_STOPPED_FRAME_THRESHOLD:
            raise EventError("Stopped frame threshold must be at least one")

    @staticmethod
    def always_pass(event_type: EventType) -> bool:
        """Return whether an already-semantic event must pass unchanged."""
        return event_type in {
            EventType.APPEARED,
            EventType.DISAPPEARED,
            EventType.STARTED_MOVING,
            EventType.STOPPED_MOVING,
        }

    @staticmethod
    def starts_movement(event_type: EventType) -> bool:
        """Return whether a raw event indicates movement."""
        return event_type is EventType.MOVED

    @staticmethod
    def stops_movement(event_type: EventType) -> bool:
        """Return whether a raw event indicates stationary behavior."""
        return event_type is EventType.STOPPED
