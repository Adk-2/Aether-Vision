"""Track identity stabilization from label history."""

from tracking import Track

from .exceptions import IdentityError
from .identity import Identity
from .label_history import LabelHistory


class IdentityResolver:
    """Maintain and update one persistent Identity per track."""

    def __init__(self) -> None:
        self._identities: dict[int, Identity] = {}

    def update(self, tracks: list[Track]) -> list[Identity]:
        """Update active track identities and return their current identities."""
        track_ids = [track.track_id for track in tracks]
        if len(track_ids) != len(set(track_ids)):
            raise IdentityError("Tracks must have unique identifiers")

        updated: list[Identity] = []
        for track in tracks:
            if not track.active:
                continue
            identity = self._update_track(track)
            track.stabilized_label = identity.current_label
            track.identity_confidence = identity.confidence
            updated.append(identity)
        return updated

    def get(self, track_id: int) -> Identity | None:
        """Return an identity, or None if the track has never been observed."""
        return self._identities.get(track_id)

    def all(self) -> list[Identity]:
        """Return all identities in first-observed order."""
        return list(self._identities.values())

    def _update_track(self, track: Track) -> Identity:
        detection = track.current_detection
        identity = self._identities.get(track.track_id)
        if identity is None:
            identity = Identity(
                track_id=track.track_id,
                current_label=detection.class_name,
                confidence=0.0,
                history=LabelHistory(),
                last_updated=detection.timestamp,
            )
            self._identities[track.track_id] = identity

        if track.missed_frames == 0:
            identity.history.add_observation(
                detection.class_name,
                detection.confidence,
            )
        identity.current_label = identity.history.best_label() or detection.class_name
        identity.confidence = identity.history.normalized_confidence(
            identity.current_label
        )
        if track.missed_frames == 0:
            identity.last_updated = detection.timestamp
        return identity
