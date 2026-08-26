"""Deterministic query layer over current tracks, memory, and timeline."""

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime

from memory import MemoryEngine, MemoryRecord
from timeline import Timeline, TimelineEntry
from tracking import Track

from .intent import Intent
from .query import QueryInterpreter
from .response import QueryResponse, QuerySource

RECENT_EVENT_LIMIT = 5


@dataclass(frozen=True)
class ObjectObservation:
    """Current observation extracted from a visible track."""

    object_name: str
    position: tuple[int, int] | None
    timestamp: datetime
    track_id: int


class QueryEngine:
    """Answer a small set of natural-language questions honestly."""

    def __init__(self, interpreter: QueryInterpreter | None = None) -> None:
        self._interpreter = interpreter or QueryInterpreter()

    def answer(
        self,
        question: str,
        current_objects: Iterable[Track],
        memory: MemoryEngine,
        timeline: Timeline,
    ) -> QueryResponse:
        """Answer a supported question from supplied state only."""
        parsed = self._interpreter.parse(question)
        current = self._current_observations(current_objects)
        if parsed.intent is Intent.CURRENT_OBJECTS:
            return self._answer_current_objects(current)
        if parsed.intent is Intent.RECENT_HISTORY:
            return self._answer_recent_history(timeline)
        if parsed.intent is Intent.UNKNOWN or parsed.object_name is None:
            return QueryResponse(
                "I don't have enough information to answer that.",
                QuerySource.UNKNOWN,
            )

        object_name = parsed.object_name
        visible = [
            observation
            for observation in current
            if observation.object_name == object_name
        ]
        records = self._records_for_object(memory, object_name)
        latest_record = self._latest_record(records)

        if parsed.intent is Intent.WHERE_IS:
            return self._answer_where_is(object_name, visible, latest_record)
        if parsed.intent is Intent.WHERE_WAS:
            return self._answer_where_was(object_name, latest_record)
        if parsed.intent is Intent.LAST_SEEN:
            return self._answer_last_seen(object_name, visible, latest_record)
        if parsed.intent is Intent.VISIBILITY:
            return self._answer_visibility(object_name, visible, latest_record)
        return QueryResponse(
            "I don't have enough information to answer that.",
            QuerySource.UNKNOWN,
        )

    def _answer_where_is(
        self,
        object_name: str,
        visible: list[ObjectObservation],
        latest_record: MemoryRecord | None,
    ) -> QueryResponse:
        if visible:
            return QueryResponse(
                self._visible_location_answer(object_name, visible),
                QuerySource.CURRENT,
            )
        if latest_record is not None:
            return QueryResponse(
                (
                    f"The {object_name} is not currently visible. "
                    f"It was last observed at approximately "
                    f"{self._position(latest_record.last_position)} at "
                    f"{self._time(latest_record.last_seen)}."
                ),
                QuerySource.MEMORY,
            )
        return self._unknown_object(object_name)

    def _answer_where_was(
        self,
        object_name: str,
        latest_record: MemoryRecord | None,
    ) -> QueryResponse:
        if latest_record is None:
            return self._unknown_object(object_name)
        return QueryResponse(
            (
                f"The {object_name} was last observed at approximately "
                f"{self._position(latest_record.last_position)} at "
                f"{self._time(latest_record.last_seen)}."
            ),
            QuerySource.MEMORY,
        )

    def _answer_last_seen(
        self,
        object_name: str,
        visible: list[ObjectObservation],
        latest_record: MemoryRecord | None,
    ) -> QueryResponse:
        if visible:
            latest_visible = max(visible, key=lambda item: item.timestamp)
            latest_time = latest_visible.timestamp
            if (
                latest_record is not None
                and latest_record.last_seen > latest_visible.timestamp
            ):
                latest_time = latest_record.last_seen
            return QueryResponse(
                (
                    f"The {object_name} was last observed at "
                    f"{self._time(latest_time)}."
                ),
                QuerySource.CURRENT,
            )
        if latest_record is None:
            return self._unknown_object(object_name)
        return QueryResponse(
            (
                f"The {object_name} was last observed at "
                f"{self._time(latest_record.last_seen)}. "
                "It is not currently visible."
            ),
            QuerySource.MEMORY,
        )

    def _answer_visibility(
        self,
        object_name: str,
        visible: list[ObjectObservation],
        latest_record: MemoryRecord | None,
    ) -> QueryResponse:
        if visible:
            return QueryResponse(
                f"Yes. The {object_name} is currently visible.",
                QuerySource.CURRENT,
            )
        if latest_record is not None:
            return QueryResponse(
                (
                    f"No. The {object_name} is not currently visible. "
                    f"Its last observation was at {self._time(latest_record.last_seen)}."
                ),
                QuerySource.MEMORY,
            )
        return self._unknown_object(object_name)

    def _answer_current_objects(
        self,
        current: list[ObjectObservation],
    ) -> QueryResponse:
        names = sorted({observation.object_name for observation in current})
        if not names:
            return QueryResponse("Currently visible:\n(none)", QuerySource.CURRENT)
        lines = ["Currently visible:", *[f"- {name}" for name in names]]
        return QueryResponse("\n".join(lines), QuerySource.CURRENT)

    def _answer_recent_history(self, timeline: Timeline) -> QueryResponse:
        entries = timeline.store.all_entries()[-RECENT_EVENT_LIMIT:]
        if not entries:
            return QueryResponse(
                "I don't have enough information to answer that.",
                QuerySource.UNKNOWN,
            )
        lines = [
            "Recently observed:",
            *[f"- {self._event_summary(entry)}" for entry in entries],
        ]
        return QueryResponse("\n".join(lines), QuerySource.TIMELINE)

    def _visible_location_answer(
        self,
        object_name: str,
        visible: list[ObjectObservation],
    ) -> str:
        if len(visible) == 1:
            return (
                f"The {object_name} is currently visible at approximately "
                f"{self._position(visible[0].position)}."
            )
        lines = [f"There are {len(visible)} {object_name}s currently visible."]
        lines.extend(
            f"- approximately {self._position(observation.position)}"
            for observation in visible
        )
        return "\n".join(lines)

    def _current_observations(
        self,
        current_objects: Iterable[Track],
    ) -> list[ObjectObservation]:
        observations: list[ObjectObservation] = []
        for track in current_objects:
            detection = track.current_detection
            object_name = self._interpreter.normalize_object(
                track.stabilized_label or detection.class_name
            )
            observations.append(
                ObjectObservation(
                    object_name=object_name,
                    position=detection.center,
                    timestamp=detection.timestamp,
                    track_id=track.track_id,
                )
            )
        return observations

    def _records_for_object(
        self,
        memory: MemoryEngine,
        object_name: str,
    ) -> list[MemoryRecord]:
        return [
            record
            for record in memory.store.list_all()
            if self._normalize_stored_object(record.object_name) == object_name
        ]

    @staticmethod
    def _latest_record(records: list[MemoryRecord]) -> MemoryRecord | None:
        return max(records, key=lambda record: record.last_seen, default=None)

    @staticmethod
    def _unknown_object(object_name: str) -> QueryResponse:
        return QueryResponse(
            f"I don't have a reliable observation of a {object_name}.",
            QuerySource.UNKNOWN,
        )

    @staticmethod
    def _position(position: tuple[int, int] | None) -> str:
        if position is None:
            return "an unknown position"
        return f"({position[0]}, {position[1]})"

    @staticmethod
    def _time(timestamp: datetime) -> str:
        return timestamp.strftime("%H:%M:%S")

    @staticmethod
    def _event_summary(entry: TimelineEntry) -> str:
        return f"{QueryEngine._display_object(entry.object_name)} {entry.event_type.value}"

    @staticmethod
    def _normalize_stored_object(object_name: str) -> str:
        return QueryInterpreter.normalize_object(
            QueryEngine._display_object(object_name)
        )

    @staticmethod
    def _display_object(object_name: str) -> str:
        label, separator, suffix = object_name.rpartition("_")
        if separator and suffix.isdigit():
            return label
        return object_name
