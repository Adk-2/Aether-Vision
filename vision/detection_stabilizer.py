"""Deterministic temporal stabilization for tracked detections."""

from __future__ import annotations

from dataclasses import replace
from typing import TYPE_CHECKING

from .label_history import LabelHistory
from .stabilization_policy import StabilizationPolicy

if TYPE_CHECKING:
    from tracking import Track


class DetectionStabilizer:
    """Stabilize noisy detector labels over time by track ID."""

    def __init__(self, policy: StabilizationPolicy | None = None) -> None:
        self.policy = policy or StabilizationPolicy()
        self._histories: dict[int, LabelHistory] = {}
        self._stable_labels: dict[int, str] = {}
        self._stable_confidences: dict[int, float] = {}

    def stabilize(self, tracks: list[Track]) -> list[Track]:
        """Update track detections in place with stable labels and confidence."""
        for track in tracks:
            if not track.active or track.missed_frames > 0:
                continue

            detection = track.current_detection
            history = self._history_for(track.track_id)
            history.add_observation(detection.class_name, detection.confidence)

            current_label = self._stable_labels.get(track.track_id)
            candidate_label = history.top_label() or detection.class_name
            stable_label = self._choose_label(
                current_label,
                candidate_label,
                history,
            )
            stable_confidence = history.normalized_confidence(stable_label)

            self._stable_labels[track.track_id] = stable_label
            self._stable_confidences[track.track_id] = stable_confidence
            stable_detection = replace(
                detection,
                class_name=stable_label,
                confidence=stable_confidence,
            )
            track.current_detection = stable_detection
            track.history[-1] = stable_detection
            track.stabilized_label = stable_label
            track.identity_confidence = stable_confidence

        return tracks

    def print_debug(self) -> None:
        """Print recent raw labels and current stable label by track."""
        print("========== Stabilizer ==========")
        if not self._histories:
            print("(empty)")
        for track_id in sorted(self._histories):
            history = self._histories[track_id]
            stable_label = self._stable_labels.get(track_id)
            confidence = self._stable_confidences.get(track_id, 0.0)
            print(f"\nTrack {track_id}\n")
            print("Raw Labels\n")
            if not history.raw_labels:
                print("(none)")
            for label in history.raw_labels:
                print(label)
            print("\nStable Label\n")
            print(stable_label or "(unknown)")
            print("\nConfidence\n")
            print(f"{confidence:.2f}")
        print("\n================================")

    def history_for(self, track_id: int) -> LabelHistory | None:
        """Return the label history for a track, if observed."""
        return self._histories.get(track_id)

    def _history_for(self, track_id: int) -> LabelHistory:
        history = self._histories.get(track_id)
        if history is None:
            history = LabelHistory(
                max_size=self.policy.history_size,
                ema_alpha=self.policy.ema_alpha,
            )
            self._histories[track_id] = history
        return history

    def _choose_label(
        self,
        current_label: str | None,
        candidate_label: str,
        history: LabelHistory,
    ) -> str:
        if current_label is None or candidate_label == current_label:
            return candidate_label
        if (
            history.vote_count(candidate_label)
            >= self.policy.minimum_votes_before_label_change
        ):
            return candidate_label
        return current_label
