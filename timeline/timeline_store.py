"""Chronological in-process storage for timeline entries."""

from .exceptions import TimelineError
from .timeline_entry import TimelineEntry


class TimelineStore:
    """Append and retrieve immutable entries in chronological order."""

    def __init__(self) -> None:
        self._entries: list[TimelineEntry] = []

    def append(self, entry: TimelineEntry) -> None:
        if self._entries:
            self._validate_next(entry)
        elif entry.sequence_number != 1:
            raise TimelineError("The first sequence number must be 1")
        self._entries.append(entry)

    def latest(self) -> TimelineEntry | None:
        return self._entries[-1] if self._entries else None

    def all_entries(self) -> list[TimelineEntry]:
        return list(self._entries)

    def entries_for_track(self, track_id: int) -> list[TimelineEntry]:
        return [entry for entry in self._entries if entry.track_id == track_id]

    def entries_for_object(self, object_name: str) -> list[TimelineEntry]:
        query = object_name.casefold()
        return [
            entry
            for entry in self._entries
            if entry.object_name.casefold() == query
        ]

    def clear(self) -> None:
        self._entries.clear()

    def _validate_next(self, entry: TimelineEntry) -> None:
        latest = self._entries[-1]
        if entry.sequence_number != latest.sequence_number + 1:
            raise TimelineError("Sequence numbers must be consecutive")
        if entry.timestamp < latest.timestamp:
            raise TimelineError("Timeline entries must be chronological")
