"""Simple query APIs for working memory."""

from datetime import datetime

from .exceptions import MemoryQueryError
from .memory_record import MemoryRecord
from .memory_store import MemoryStore


def get_by_track_id(store: MemoryStore, track_id: int) -> MemoryRecord:
    record = store.get_by_track_id(track_id)
    if record is None:
        raise MemoryQueryError(f"Unknown track ID: {track_id}")
    return record


def get_by_name(store: MemoryStore, object_name: str) -> MemoryRecord:
    record = store.get_by_name(object_name)
    if record is None:
        raise MemoryQueryError(f"Unknown object name: {object_name}")
    return record


def last_seen(store: MemoryStore, track_id: int) -> datetime:
    return get_by_track_id(store, track_id).last_seen


def last_position(
    store: MemoryStore,
    track_id: int,
) -> tuple[int, int] | None:
    return get_by_track_id(store, track_id).last_position


def list_objects(store: MemoryStore) -> list[MemoryRecord]:
    return store.list_all()
