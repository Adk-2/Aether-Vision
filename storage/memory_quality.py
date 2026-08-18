"""Quality controls for persisted episodic memory."""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timedelta

from events import Event, EventType
from memory import MemoryRecord
from timeline import TimelineEntry

from .serializer import PersistentMemory

DEFAULT_MOVEMENT_DEBOUNCE_SECONDS = 2.0

_IMPORTANT_EVENT_TYPES = {
    EventType.APPEARED,
    EventType.DISAPPEARED,
    EventType.STARTED_MOVING,
    EventType.STOPPED_MOVING,
}
_MOVEMENT_TRANSITIONS = {
    EventType.STARTED_MOVING,
    EventType.STOPPED_MOVING,
}


def compact_persistent_memory(
    memory: PersistentMemory,
    movement_debounce_seconds: float = DEFAULT_MOVEMENT_DEBOUNCE_SECONDS,
) -> PersistentMemory:
    """Return a persistence-focused snapshot with repetitive movement collapsed."""
    history_suppressed = 0
    objects = _dedupe_records(memory.objects)
    compacted_objects: list[MemoryRecord] = []
    for record in objects:
        history, count = _compact_events(record.history, movement_debounce_seconds)
        history_suppressed += count
        compacted_objects.append(replace(record, history=history))

    timeline_entries, timeline_suppressed = _compact_timeline(
        memory.timeline_entries,
        movement_debounce_seconds,
    )
    suppressed = max(history_suppressed, timeline_suppressed)

    return PersistentMemory(
        objects=compacted_objects,
        timeline_entries=timeline_entries,
        beliefs=memory.beliefs,
        source=memory.source,
        movement_noise_suppressed=memory.movement_noise_suppressed + suppressed,
    )


def _dedupe_records(records: list[MemoryRecord]) -> list[MemoryRecord]:
    latest_by_key: dict[str, MemoryRecord] = {}
    for record in records:
        key = _record_identity_key(record)
        current = latest_by_key.get(key)
        if current is None or record.last_seen >= current.last_seen:
            latest_by_key[key] = record
    return sorted(latest_by_key.values(), key=lambda item: item.last_seen)


def _record_identity_key(record: MemoryRecord) -> str:
    label, separator, suffix = record.object_name.rpartition("_")
    if separator and suffix.isdigit():
        return record.object_name.casefold()
    return _logical_name(record.object_name).casefold()


def _compact_events(
    events: list[Event],
    movement_debounce_seconds: float,
) -> tuple[list[Event], int]:
    last_movement_at: dict[str, datetime] = {}
    compacted: list[Event] = []
    suppressed = 0
    for event in events:
        if event.event_type not in _IMPORTANT_EVENT_TYPES:
            continue
        if _should_suppress_movement(
            event,
            last_movement_at,
            movement_debounce_seconds,
        ):
            suppressed += 1
            continue
        compacted.append(event)
    return compacted, suppressed


def _compact_timeline(
    entries: list[TimelineEntry],
    movement_debounce_seconds: float,
) -> tuple[list[TimelineEntry], int]:
    last_movement_at: dict[str, datetime] = {}
    compacted: list[TimelineEntry] = []
    suppressed = 0
    for entry in entries:
        if entry.event_type not in _IMPORTANT_EVENT_TYPES:
            continue
        if _should_suppress_movement(
            entry,
            last_movement_at,
            movement_debounce_seconds,
        ):
            suppressed += 1
            continue
        compacted.append(entry)
    return (
        [_renumber_entry(entry, index) for index, entry in enumerate(compacted, 1)],
        suppressed,
    )


def _should_suppress_movement(
    item: Event | TimelineEntry,
    last_movement_at: dict[str, datetime],
    movement_debounce_seconds: float,
) -> bool:
    if item.event_type not in _MOVEMENT_TRANSITIONS:
        return False
    key = _logical_name(item.object_name or item.description).casefold()
    previous = last_movement_at.get(key)
    last_movement_at[key] = item.timestamp
    if previous is None:
        return False
    return item.timestamp - previous < timedelta(seconds=movement_debounce_seconds)


def _renumber_entry(entry: TimelineEntry, sequence_number: int) -> TimelineEntry:
    return replace(entry, sequence_number=sequence_number)


def _logical_name(object_name: str) -> str:
    label, separator, suffix = object_name.rpartition("_")
    return label if separator and suffix.isdigit() else object_name
