"""Detection of changes between consecutive world snapshots."""

from tracking import Track
from world.snapshot import WorldSnapshot

from .event import Event
from .event_types import EventType
from .exceptions import EventError

DEFAULT_STOPPED_FRAME_THRESHOLD = 3
MINIMUM_STOPPED_FRAME_THRESHOLD = 1
TRACK_ID_WIDTH = 3


class EventEngine:
    """Generate events from consecutive snapshots without retaining history."""

    def __init__(
        self,
        stopped_frame_threshold: int = DEFAULT_STOPPED_FRAME_THRESHOLD,
    ) -> None:
        if stopped_frame_threshold < MINIMUM_STOPPED_FRAME_THRESHOLD:
            raise EventError("Stopped frame threshold must be at least one")
        self._stopped_frame_threshold = stopped_frame_threshold
        self._unchanged_frames: dict[int, int] = {}

    def generate_events(
        self,
        previous: WorldSnapshot | None,
        current: WorldSnapshot,
    ) -> list[Event]:
        """Compare snapshots and return every change observed."""
        previous_tracks = self._index(previous.tracks if previous else ())
        current_tracks = self._index(current.tracks)
        events: list[Event] = []

        for track_id, track in current_tracks.items():
            old_track = previous_tracks.get(track_id)
            if old_track is None:
                self._unchanged_frames[track_id] = 0
                events.append(self._event(EventType.APPEARED, track, current))
            else:
                events.extend(self._movement_events(old_track, track, current))

        for track_id, track in previous_tracks.items():
            if track_id not in current_tracks:
                self._unchanged_frames.pop(track_id, None)
                events.append(self._event(EventType.DISAPPEARED, track, current))
        return events

    def generate(
        self,
        previous: WorldSnapshot | None,
        current: WorldSnapshot,
    ) -> list[Event]:
        """Provide a concise alias for generate_events."""
        return self.generate_events(previous, current)

    def _movement_events(
        self,
        previous: Track,
        current: Track,
        snapshot: WorldSnapshot,
    ) -> list[Event]:
        """Generate movement or stopped events for a continuing track."""
        if previous.current_detection.center != current.current_detection.center:
            self._unchanged_frames[current.track_id] = 0
            return [self._event(EventType.MOVED, current, snapshot)]

        unchanged = self._unchanged_frames.get(current.track_id, 0) + 1
        self._unchanged_frames[current.track_id] = unchanged
        if unchanged == self._stopped_frame_threshold:
            return [self._event(EventType.STOPPED, current, snapshot)]
        return []

    @staticmethod
    def _index(tracks: tuple[Track, ...]) -> dict[int, Track]:
        """Index snapshot tracks and reject ambiguous identifiers."""
        indexed = {track.track_id: track for track in tracks}
        if len(indexed) != len(tracks):
            raise EventError("Snapshot tracks must have unique identifiers")
        return indexed

    @staticmethod
    def _event(
        event_type: EventType,
        track: Track,
        snapshot: WorldSnapshot,
    ) -> Event:
        """Build a human-readable event for one track."""
        object_name = (
            f"{track.current_detection.class_name}_"
            f"{track.track_id:0{TRACK_ID_WIDTH}d}"
        )
        return Event(
            event_type=event_type,
            track_id=track.track_id,
            timestamp=snapshot.timestamp,
            description=f"{object_name} {event_type.value}",
            object_name=object_name,
            position=track.current_detection.center,
        )
