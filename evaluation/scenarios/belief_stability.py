"""Measured benchmark for belief stability under seeded label noise."""

from belief import BeliefEngine
from evaluation.benchmark import Benchmark
from evaluation.metrics import Score
from evaluation.scenarios.common import (
    MultiTrackFrame,
    noisy_multitrack_stream,
    relabel_stream,
    track,
)
from identity import IdentityResolver

RELABEL_CHANGE_FRAME = 15


def evaluate(
    frames: list[MultiTrackFrame] | None = None,
    adaptation_frames: list[MultiTrackFrame] | None = None,
) -> Benchmark:
    """Run real identity and belief components on seeded noisy detections."""
    scripted_frames = noisy_multitrack_stream() if frames is None else frames
    scripted_adaptation = relabel_stream() if adaptation_frames is None else adaptation_frames
    resolver = IdentityResolver()
    beliefs = BeliefEngine()
    correct = 0
    total = 0

    for frame_index, frame in enumerate(scripted_frames):
        tracks = [
            track(
                observation.label,
                track_id=observation.track_id,
                frame_index=frame_index,
                center=observation.center,
                confidence=observation.confidence,
            )
            for observation in frame.observations
        ]
        identities = resolver.update(tracks)
        states = {state.track_id: state for state in beliefs.update(identities)}
        for observation in frame.observations:
            total += 1
            if states[observation.track_id].current_belief == observation.expected_label:
                correct += 1

    frames_to_switch = _frames_until_switch(scripted_adaptation)
    adaptation_success = 1 if frames_to_switch is not None else 0
    noise_score = Score(
        correct / total if total else 0.0,
        correct,
        total,
        "noise-suppressed frames",
    )
    adaptation_score = Score(
        float(adaptation_success),
        adaptation_success,
        1,
        "adaptation cases",
    )
    return Benchmark(
        name="Belief Stability",
        description=(
            "Real IdentityResolver plus BeliefEngine on a fixed-seed >=200-frame, "
            "two-track noisy stream including a low-confidence noise burst; "
            "adaptation is measured on a 15-frame cup then 15-frame bottle relabel."
        ),
        expected_result=(
            "Beliefs should match ground truth during noisy frames and switch after "
            "a real relabel."
        ),
        actual_result=(
            f"noise_suppression={correct}/{total}; "
            f"frames_until_relabel_switch={frames_to_switch if frames_to_switch is not None else 'not switched'}."
        ),
        score=noise_score,
        metrics=(noise_score, adaptation_score),
    )


def run() -> Benchmark:
    """Return the measured belief stability benchmark."""
    return evaluate()


def _frames_until_switch(frames: list[MultiTrackFrame]) -> int | None:
    resolver = IdentityResolver()
    beliefs = BeliefEngine()
    for frame_index, frame in enumerate(frames):
        observation = frame.observations[0]
        identities = resolver.update([
            track(
                observation.label,
                track_id=observation.track_id,
                frame_index=frame_index,
                center=observation.center,
                confidence=observation.confidence,
            )
        ])
        states = beliefs.update(identities)
        if (
            frame_index >= RELABEL_CHANGE_FRAME
            and states[0].current_belief == observation.expected_label
        ):
            return frame_index - RELABEL_CHANGE_FRAME + 1
    return None
