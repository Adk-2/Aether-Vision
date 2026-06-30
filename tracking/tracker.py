"""Persistent object identity lifecycle management."""

from vision.detection import Detection

from .association import (
    AssociationEngine,
    AssociationStrategy,
    DEFAULT_DISTANCE_THRESHOLD,
)
from .exceptions import TrackingError
from .track import Track

DEFAULT_MISSED_FRAME_LIMIT = 5
MINIMUM_MISSED_FRAME_LIMIT = 1
FIRST_TRACK_ID = 0
INITIAL_TRACK_AGE = 1
INITIAL_MISSED_FRAMES = 0


class Tracker:
    """Create, update, and deactivate persistent object tracks."""

    def __init__(
        self,
        association_engine: AssociationStrategy | None = None,
        distance_threshold: float = DEFAULT_DISTANCE_THRESHOLD,
        missed_frame_limit: int = DEFAULT_MISSED_FRAME_LIMIT,
    ) -> None:
        """Initialize tracking configuration and empty track storage."""
        if missed_frame_limit < MINIMUM_MISSED_FRAME_LIMIT:
            raise TrackingError("Missed frame limit must be at least one")
        self._association_engine = association_engine or AssociationEngine(
            distance_threshold
        )
        self._missed_frame_limit = missed_frame_limit
        self._next_track_id = FIRST_TRACK_ID
        self._tracks: list[Track] = []

    def update(self, detections: list[Detection]) -> list[Track]:
        """Update tracks with detections and return all active tracks."""
        matched_pairs, unmatched_tracks, unmatched_detections = (
            self._association_engine.associate(
                self.get_active_tracks(),
                detections,
            )
        )
        for track, detection in matched_pairs:
            self._update_matched_track(track, detection)
        for track in unmatched_tracks:
            self._update_unmatched_track(track)
        for detection in unmatched_detections:
            self._tracks.append(self._create_track(detection))
        return self.get_active_tracks()

    def get_active_tracks(self) -> list[Track]:
        """Return all tracks that have not been deactivated."""
        return [track for track in self._tracks if track.active]

    @staticmethod
    def _update_matched_track(track: Track, detection: Detection) -> None:
        """Apply a newly associated detection to an existing track."""
        track.current_detection = detection
        track.history.append(detection)
        track.last_seen = detection.timestamp
        track.age += 1
        track.missed_frames = INITIAL_MISSED_FRAMES

    def _update_unmatched_track(self, track: Track) -> None:
        """Age an unmatched track and deactivate it at the miss limit."""
        track.age += 1
        track.missed_frames += 1
        if track.missed_frames >= self._missed_frame_limit:
            track.active = False

    def _create_track(self, detection: Detection) -> Track:
        """Create a new active track for an unmatched detection."""
        track = Track(
            track_id=self._next_track_id,
            current_detection=detection,
            history=[detection],
            first_seen=detection.timestamp,
            last_seen=detection.timestamp,
            age=INITIAL_TRACK_AGE,
            missed_frames=INITIAL_MISSED_FRAMES,
            active=True,
        )
        self._next_track_id += 1
        return track
