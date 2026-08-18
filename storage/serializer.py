"""JSON serialization helpers for Project Aether memory."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from belief import BeliefState
from events import Event, EventType
from memory import MemoryRecord, MemoryStatus
from timeline import TimelineEntry

SCHEMA_VERSION = 1


@dataclass
class PersistentMemory:
    """Serializable snapshot of persisted Aether state."""

    objects: list[MemoryRecord] = field(default_factory=list)
    timeline_entries: list[TimelineEntry] = field(default_factory=list)
    beliefs: list[BeliefState] = field(default_factory=list)
    source: str = "Previous Sessions"
    movement_noise_suppressed: int = 0


def empty_memory() -> PersistentMemory:
    """Return an empty persistent memory snapshot."""
    return PersistentMemory()


def to_json(memory: PersistentMemory) -> dict[str, Any]:
    """Convert persistent memory into human-readable JSON data."""
    return {
        "schema_version": SCHEMA_VERSION,
        "memory_source": memory.source,
        "objects": [_record_to_json(record) for record in memory.objects],
        "timeline": [_entry_to_json(entry) for entry in memory.timeline_entries],
        "beliefs": [_belief_to_json(state) for state in memory.beliefs],
        "movement_noise_suppressed": memory.movement_noise_suppressed,
    }


def from_json(data: dict[str, Any]) -> PersistentMemory:
    """Convert JSON data into a persistent memory snapshot."""
    if not isinstance(data, dict):
        return empty_memory()
    return PersistentMemory(
        objects=[
            record
            for item in data.get("objects", [])
            if isinstance(item, dict)
            for record in [_record_from_json(item)]
            if record is not None
        ],
        timeline_entries=[
            entry
            for item in data.get("timeline", [])
            if isinstance(item, dict)
            for entry in [_entry_from_json(item)]
            if entry is not None
        ],
        beliefs=[
            state
            for item in data.get("beliefs", [])
            if isinstance(item, dict)
            for state in [_belief_from_json(item)]
            if state is not None
        ],
        source=str(data.get("memory_source") or "Previous Sessions"),
        movement_noise_suppressed=_parse_int(
            data.get("movement_noise_suppressed"),
            default=0,
        ),
    )


def _record_to_json(record: MemoryRecord) -> dict[str, Any]:
    return {
        "track_id": record.track_id,
        "object_name": record.object_name,
        "status": record.status.value,
        "first_seen": record.first_seen.isoformat(),
        "last_seen": record.last_seen.isoformat(),
        "last_position": list(record.last_position) if record.last_position else None,
        "confidence": record.confidence,
        "history": [_event_to_json(event) for event in record.history],
    }


def _record_from_json(data: dict[str, Any]) -> MemoryRecord | None:
    try:
        history = [
            event
            for item in data.get("history", [])
            if isinstance(item, dict)
            for event in [_event_from_json(item)]
            if event is not None
        ]
        return MemoryRecord(
            track_id=int(data["track_id"]),
            object_name=str(data["object_name"]),
            first_seen=_parse_datetime(data["first_seen"]),
            last_seen=_parse_datetime(data["last_seen"]),
            last_position=_parse_position(data.get("last_position")),
            status=MemoryStatus(str(data["status"])),
            history=history,
            confidence=_parse_optional_float(data.get("confidence")),
            restored=True,
        )
    except (KeyError, TypeError, ValueError):
        return None


def _event_to_json(event: Event) -> dict[str, Any]:
    return {
        "event_type": event.event_type.value,
        "track_id": event.track_id,
        "timestamp": event.timestamp.isoformat(),
        "description": event.description,
        "object_name": event.object_name,
        "position": list(event.position) if event.position else None,
    }


def _event_from_json(data: dict[str, Any]) -> Event | None:
    try:
        return Event(
            event_type=EventType(str(data["event_type"])),
            track_id=int(data["track_id"]),
            timestamp=_parse_datetime(data["timestamp"]),
            description=str(data["description"]),
            object_name=(
                str(data["object_name"])
                if data.get("object_name") is not None
                else None
            ),
            position=_parse_position(data.get("position")),
        )
    except (KeyError, TypeError, ValueError):
        return None


def _entry_to_json(entry: TimelineEntry) -> dict[str, Any]:
    return {
        "sequence_number": entry.sequence_number,
        "timestamp": entry.timestamp.isoformat(),
        "track_id": entry.track_id,
        "object_name": entry.object_name,
        "event_type": entry.event_type.value,
        "description": entry.description,
    }


def _entry_from_json(data: dict[str, Any]) -> TimelineEntry | None:
    try:
        return TimelineEntry(
            sequence_number=int(data["sequence_number"]),
            timestamp=_parse_datetime(data["timestamp"]),
            track_id=int(data["track_id"]),
            object_name=str(data["object_name"]),
            event_type=EventType(str(data["event_type"])),
            description=str(data["description"]),
        )
    except (KeyError, TypeError, ValueError):
        return None


def _belief_to_json(state: BeliefState) -> dict[str, Any]:
    return {
        "track_id": state.track_id,
        "current_belief": state.current_belief,
        "confidence": state.confidence,
        "stable_since": state.stable_since.isoformat(),
        "frames_stable": state.frames_stable,
        "alternative_beliefs": state.alternative_beliefs,
    }


def _belief_from_json(data: dict[str, Any]) -> BeliefState | None:
    try:
        alternatives = data.get("alternative_beliefs", {})
        return BeliefState(
            track_id=int(data["track_id"]),
            current_belief=str(data["current_belief"]),
            confidence=float(data["confidence"]),
            stable_since=_parse_datetime(data["stable_since"]),
            frames_stable=int(data["frames_stable"]),
            alternative_beliefs={
                str(label): float(confidence)
                for label, confidence in alternatives.items()
            }
            if isinstance(alternatives, dict)
            else {},
        )
    except (KeyError, TypeError, ValueError):
        return None


def _parse_datetime(value: Any) -> datetime:
    if not isinstance(value, str):
        raise ValueError("Expected ISO datetime string")
    return datetime.fromisoformat(value)


def _parse_position(value: Any) -> tuple[int, int] | None:
    if value is None:
        return None
    if not isinstance(value, list | tuple) or len(value) != 2:
        raise ValueError("Expected 2D position")
    return int(value[0]), int(value[1])


def _parse_optional_float(value: Any) -> float | None:
    return None if value is None else float(value)


def _parse_int(value: Any, default: int) -> int:
    try:
        return default if value is None else int(value)
    except (TypeError, ValueError):
        return default
