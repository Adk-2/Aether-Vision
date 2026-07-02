"""Simple query APIs for the episodic timeline."""

from .exceptions import TimelineQueryError
from .timeline_entry import TimelineEntry
from .timeline_store import TimelineStore


def recent_events(store: TimelineStore, limit: int) -> list[TimelineEntry]:
    if limit < 0:
        raise TimelineQueryError("Event limit cannot be negative")
    if limit == 0:
        return []
    return store.all_entries()[-limit:]


def events_for_track(
    store: TimelineStore,
    track_id: int,
) -> list[TimelineEntry]:
    return store.entries_for_track(track_id)


def events_for_object(
    store: TimelineStore,
    name: str,
) -> list[TimelineEntry]:
    return store.entries_for_object(name)


def latest_event(store: TimelineStore) -> TimelineEntry:
    entry = store.latest()
    if entry is None:
        raise TimelineQueryError("Timeline is empty")
    return entry
