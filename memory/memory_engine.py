"""Event-driven working-memory updates."""

from events import Event, EventType

from .exceptions import MemoryError
from .memory_record import MemoryRecord, MemoryStatus
from .memory_store import MemoryStore

_STATUS_BY_EVENT = {
    EventType.APPEARED: MemoryStatus.ACTIVE,
    EventType.MOVED: MemoryStatus.MOVING,
    EventType.STOPPED: MemoryStatus.STATIC,
    EventType.DISAPPEARED: MemoryStatus.LOST,
}


class MemoryEngine:
    """Maintain working memory using events as its only input."""

    def __init__(self, store: MemoryStore | None = None) -> None:
        self.store = store or MemoryStore()

    def process(self, events: list[Event]) -> None:
        for event in events:
            self.process_event(event)

    def process_event(self, event: Event) -> None:
        record = self.store.get_by_track_id(event.track_id)
        if record is None:
            self.store.add(self._new_record(event))
            return
        record.last_seen = event.timestamp
        record.status = _STATUS_BY_EVENT[event.event_type]
        if event.position is not None:
            record.last_position = event.position
        record.history.append(event)
        self.store.update(record)

    @staticmethod
    def _new_record(event: Event) -> MemoryRecord:
        if event.event_type is not EventType.APPEARED:
            raise MemoryError(f"Track {event.track_id} has no APPEARED event")
        object_name = event.object_name or event.description.split(maxsplit=1)[0]
        return MemoryRecord(
            track_id=event.track_id,
            object_name=object_name,
            first_seen=event.timestamp,
            last_seen=event.timestamp,
            last_position=event.position,
            status=MemoryStatus.ACTIVE,
            history=[event],
        )
