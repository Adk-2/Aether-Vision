"""Event-driven episodic timeline engine."""

from events import Event

from .timeline_entry import TimelineEntry
from .timeline_store import TimelineStore


class Timeline:
    """Convert event lists into chronological timeline entries."""

    def __init__(self, store: TimelineStore | None = None) -> None:
        self.store = store or TimelineStore()

    def process(self, events: list[Event]) -> None:
        for event in events:
            self.append_event(event)

    def append_event(self, event: Event) -> None:
        latest = self.store.latest()
        sequence_number = latest.sequence_number + 1 if latest else 1
        object_name = event.object_name or event.description.split(maxsplit=1)[0]
        self.store.append(
            TimelineEntry(
                sequence_number=sequence_number,
                timestamp=event.timestamp,
                track_id=event.track_id,
                object_name=object_name,
                event_type=event.event_type,
                description=event.description,
            )
        )
