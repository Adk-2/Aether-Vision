"""Current and immediately previous world state management."""

from copy import deepcopy
from datetime import datetime

from events.exceptions import WorldStateError
from tracking import Track

from .object_registry import ObjectRegistry
from .snapshot import WorldSnapshot


class WorldState:
    """Maintain only the current and previous snapshots of active tracks."""

    def __init__(self, registry: ObjectRegistry | None = None) -> None:
        self._registry = registry or ObjectRegistry()
        self._previous_snapshot: WorldSnapshot | None = None
        self._current_snapshot: WorldSnapshot | None = None

    @property
    def current_snapshot(self) -> WorldSnapshot | None:
        """Return the latest snapshot, if the world has been updated."""
        return self._current_snapshot

    @property
    def previous_snapshot(self) -> WorldSnapshot | None:
        """Return the snapshot immediately preceding the current one."""
        return self._previous_snapshot

    def update(
        self,
        tracks: list[Track],
        timestamp: datetime | None = None,
    ) -> WorldSnapshot:
        """Replace the active world and create a detached snapshot."""
        track_ids = [track.track_id for track in tracks]
        if len(track_ids) != len(set(track_ids)):
            raise WorldStateError("Active tracks must have unique track identifiers")

        self._registry.clear()
        for track in tracks:
            if track.active:
                self._registry.register(track)

        snapshot_tracks = deepcopy(self._registry.values())
        snapshot_time = timestamp or self._infer_timestamp(snapshot_tracks)
        snapshot = WorldSnapshot(
            timestamp=snapshot_time,
            tracks=snapshot_tracks,
            active_track_count=len(snapshot_tracks),
        )
        self._previous_snapshot = self._current_snapshot
        self._current_snapshot = snapshot
        return snapshot

    @staticmethod
    def _infer_timestamp(tracks: tuple[Track, ...]) -> datetime:
        """Infer snapshot time from tracks when the caller omits it."""
        if not tracks:
            raise WorldStateError("A timestamp is required for an empty world")
        return max(track.last_seen for track in tracks)
