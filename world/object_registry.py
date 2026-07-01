"""Lookup registry for active tracks."""

from tracking import Track


class ObjectRegistry:
    """Maintain active tracks indexed by their persistent identifiers."""

    def __init__(self) -> None:
        self._tracks: dict[int, Track] = {}

    def register(self, track: Track) -> None:
        """Add or replace a track in the registry."""
        self._tracks[track.track_id] = track

    def remove(self, track_id: int) -> None:
        """Remove a track if it is registered."""
        self._tracks.pop(track_id, None)

    def exists(self, track_id: int) -> bool:
        """Return whether a track identifier is registered."""
        return track_id in self._tracks

    def get(self, track_id: int) -> Track | None:
        """Return a registered track, or None when it is absent."""
        return self._tracks.get(track_id)

    def clear(self) -> None:
        """Remove all registered tracks."""
        self._tracks.clear()

    def values(self) -> tuple[Track, ...]:
        """Return registered tracks in insertion order."""
        return tuple(self._tracks.values())
