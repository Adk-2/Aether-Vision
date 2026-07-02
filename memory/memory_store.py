"""In-process storage for working-memory records."""

from .memory_record import MemoryRecord


class MemoryStore:
    """Store working-memory records indexed by track identifier."""

    def __init__(self) -> None:
        self._records: dict[int, MemoryRecord] = {}

    def add(self, record: MemoryRecord) -> None:
        self._records[record.track_id] = record

    def update(self, record: MemoryRecord) -> None:
        self._records[record.track_id] = record

    def remove(self, track_id: int) -> MemoryRecord | None:
        return self._records.pop(track_id, None)

    def get_by_track_id(self, track_id: int) -> MemoryRecord | None:
        return self._records.get(track_id)

    def get_by_name(self, object_name: str) -> MemoryRecord | None:
        query = object_name.casefold()
        return next(
            (
                record
                for record in self._records.values()
                if record.object_name.casefold() == query
            ),
            None,
        )

    def list_all(self) -> list[MemoryRecord]:
        return list(self._records.values())

    def clear(self) -> None:
        self._records.clear()
