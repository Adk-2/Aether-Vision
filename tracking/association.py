"""Nearest-neighbour association for tracks and detections."""

from typing import Protocol, TypeAlias

from vision.detection import Detection

from .distance import euclidean_distance
from .exceptions import AssociationError
from .track import Track

DEFAULT_DISTANCE_THRESHOLD = 50.0
MINIMUM_DISTANCE_THRESHOLD = 0.0

MatchedPair: TypeAlias = tuple[Track, Detection]
AssociationResult: TypeAlias = tuple[
    list[MatchedPair],
    list[Track],
    list[Detection],
]


class AssociationStrategy(Protocol):
    """Define the replaceable association contract used by Tracker."""

    def associate(
        self,
        tracks: list[Track],
        detections: list[Detection],
    ) -> AssociationResult:
        """Return matched and unmatched tracks and detections."""
        ...


class AssociationEngine:
    """Associate detections and tracks using nearest-neighbour distance."""

    def __init__(
        self,
        distance_threshold: float = DEFAULT_DISTANCE_THRESHOLD,
    ) -> None:
        """Initialize association with a maximum center distance."""
        if distance_threshold < MINIMUM_DISTANCE_THRESHOLD:
            raise AssociationError("Distance threshold cannot be negative")
        self._distance_threshold = distance_threshold

    def associate(
        self,
        tracks: list[Track],
        detections: list[Detection],
    ) -> AssociationResult:
        """Return matches and unmatched inputs using one-to-one matching."""
        candidates = self._build_candidates(tracks, detections)
        matched_track_indexes: set[int] = set()
        matched_detection_indexes: set[int] = set()
        matched_pairs: list[MatchedPair] = []

        for _, track_index, detection_index in candidates:
            if track_index in matched_track_indexes:
                continue
            if detection_index in matched_detection_indexes:
                continue
            matched_pairs.append((tracks[track_index], detections[detection_index]))
            matched_track_indexes.add(track_index)
            matched_detection_indexes.add(detection_index)

        unmatched_tracks = [
            track
            for index, track in enumerate(tracks)
            if index not in matched_track_indexes
        ]
        unmatched_detections = [
            detection
            for index, detection in enumerate(detections)
            if index not in matched_detection_indexes
        ]
        return matched_pairs, unmatched_tracks, unmatched_detections

    def _build_candidates(
        self,
        tracks: list[Track],
        detections: list[Detection],
    ) -> list[tuple[float, int, int]]:
        """Build candidate pairs ordered by increasing center distance."""
        candidates: list[tuple[float, int, int]] = []
        for track_index, track in enumerate(tracks):
            for detection_index, detection in enumerate(detections):
                distance = euclidean_distance(
                    track.current_detection.center,
                    detection.center,
                )
                if distance <= self._distance_threshold:
                    candidates.append((distance, track_index, detection_index))
        return sorted(candidates, key=lambda candidate: candidate[0])
