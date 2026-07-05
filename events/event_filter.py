"""Behavioral stabilization for generated events."""

from dataclasses import replace
from enum import Enum

from .event import Event
from .event_policy import EventPolicy
from .event_types import EventType


class MovementState(Enum):
    """Describe whether a tracked object is currently moving."""

    STATIC = "static"
    MOVING = "moving"


class EventFilter:
    """Suppress redundant events and emit movement transitions."""

    def __init__(self, policy: EventPolicy | None = None) -> None:
        self._policy = policy or EventPolicy()
        self._movement_states: dict[int, MovementState] = {}

    def filter_events(self, events: list[Event]) -> list[Event]:
        """Return only meaningful behavioral transitions."""
        filtered: list[Event] = []
        for event in events:
            stabilized = self._filter_event(event)
            if stabilized is not None:
                filtered.append(stabilized)
        return filtered

    def filter(self, events: list[Event]) -> list[Event]:
        """Provide a concise alias for filter_events."""
        return self.filter_events(events)

    def _filter_event(self, event: Event) -> Event | None:
        if event.event_type is EventType.APPEARED:
            self._movement_states[event.track_id] = MovementState.STATIC
            return event
        if event.event_type is EventType.DISAPPEARED:
            self._movement_states.pop(event.track_id, None)
            return event
        if self._policy.starts_movement(event.event_type):
            return self._started_moving(event)
        if self._policy.stops_movement(event.event_type):
            return self._stopped_moving(event)
        if self._policy.always_pass(event.event_type):
            self._record_semantic_state(event)
            return event
        return event

    def _started_moving(self, event: Event) -> Event | None:
        if self._state(event.track_id) is MovementState.MOVING:
            return None
        self._movement_states[event.track_id] = MovementState.MOVING
        return self._as_transition(event, EventType.STARTED_MOVING)

    def _stopped_moving(self, event: Event) -> Event | None:
        if self._state(event.track_id) is MovementState.STATIC:
            return None
        self._movement_states[event.track_id] = MovementState.STATIC
        return self._as_transition(event, EventType.STOPPED_MOVING)

    def _record_semantic_state(self, event: Event) -> None:
        if event.event_type is EventType.STARTED_MOVING:
            self._movement_states[event.track_id] = MovementState.MOVING
        elif event.event_type is EventType.STOPPED_MOVING:
            self._movement_states[event.track_id] = MovementState.STATIC

    def _state(self, track_id: int) -> MovementState:
        return self._movement_states.get(track_id, MovementState.STATIC)

    @staticmethod
    def _as_transition(event: Event, event_type: EventType) -> Event:
        object_name = event.object_name or event.description.split(maxsplit=1)[0]
        return replace(
            event,
            event_type=event_type,
            description=f"{object_name} {event_type.value}",
        )
