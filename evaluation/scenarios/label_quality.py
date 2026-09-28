"""Shared measurements; truth comes from scripted observations, never predictions."""

from statistics import mean
from evaluation.benchmark import Benchmark
from evaluation.metrics import Measurement, Score
from evaluation.scenarios.common import noisy_multitrack_stream, relabel_stream, track
from identity import IdentityResolver
from belief import BeliefEngine

SEEDS = tuple(range(20260920, 20260940))


def predictions(frames):
    if not frames or not any(f.observations for f in frames):
        raise ValueError("No label observations")
    resolver, beliefs = IdentityResolver(), BeliefEngine()
    for index, frame in enumerate(frames):
        tracks = [
            track(
                o.label,
                track_id=o.track_id,
                frame_index=index,
                center=o.center,
                confidence=o.confidence,
            )
            for o in frame.observations
        ]
        identities = resolver.update(tracks)
        states = beliefs.update(identities)
        yield (
            {x.track_id: x.current_label for x in identities},
            {x.track_id: x.current_belief for x in states},
        )


def noise_measurements(frames, component):
    ages, first_correct = {}, {}
    correct = total = 0
    for frame, outputs in zip(frames, predictions(frames), strict=True):
        for o in frame.observations:
            age = ages.get(o.track_id, 0) + 1
            ages[o.track_id] = age
            matches = outputs[component].get(o.track_id) == o.expected_label
            if matches:
                first_correct.setdefault(o.track_id, age)
            if age > 15:
                total += 1
                correct += matches
    if not total:
        raise ValueError("No steady-state observations after first 15 per track")
    cold = [first_correct.get(t, f">{age}") for t, age in ages.items()]
    return correct, total, cold


def frames_until_switch(frames, component):
    for index, (frame, outputs) in enumerate(
        zip(frames, predictions(frames), strict=True)
    ):
        if index >= 30 and all(
            outputs[component].get(o.track_id) == o.expected_label
            for o in frame.observations
        ):
            return index - 30 + 1
    return ">100"


def burst_tolerance(expected_label="cup"):
    """30 clean frames establish a track; inspect every burst frame and 30 recovery frames.
    Ground truth remains cup throughout; wrong observations have confidence 0.9.
    """
    from evaluation.scenarios.common import MultiTrackFrame, LabelObservation

    safe = []
    for length in range(1, 21):
        labels = ["cup"] * 30 + ["bottle"] * length + ["cup"] * 30
        frames = [
            MultiTrackFrame(
                (LabelObservation(1, label, 0.9, expected_label, (100, 200)),)
            )
            for label in labels
        ]
        outputs = list(predictions(frames))
        safe.append(
            all(
                a.get(1) == expected_label and b.get(1) == expected_label
                for a, b in outputs[30:]
            )
        )
    return max((i + 1 for i, passed in enumerate(safe) if passed), default=0)


def evaluate(component, frames=None, adaptation_frames=None, seeds=SEEDS):
    if not seeds:
        raise ValueError("No seeds")
    streams = (
        [noisy_multitrack_stream(seed) for seed in seeds]
        if frames is None
        else [frames]
    )
    results = [noise_measurements(stream, component) for stream in streams]
    accuracies = [correct / total for correct, total, _ in results]
    cold = [value for _, _, values in results for value in values]
    correct, total = sum(r[0] for r in results), sum(r[1] for r in results)
    score = Score(correct / total, correct, total, "steady-state pooled accuracy")
    metrics = [score]
    for label, fn in [("mean", mean), ("min", min), ("max", max)]:
        metrics.append(
            Measurement(f"steady-state accuracy {label}", fn(accuracies) * 100, "%")
        )
        metrics.append(
            Measurement(
                f"cold start {label}",
                fn(cold)
                if all(isinstance(v, int) for v in cold)
                else "n/a (censored: " + ", ".join(map(str, cold)) + ")",
                "frames",
            )
        )
    adaptation = relabel_stream() if adaptation_frames is None else adaptation_frames
    switch = frames_until_switch(adaptation, component)
    metrics.extend(
        [
            Measurement("frames until switch", switch, "frames"),
            Measurement(
                "largest burst neither identity nor belief flips",
                burst_tolerance(),
                "frames",
            ),
        ]
    )
    return Benchmark(
        "Identity Stability" if component == 0 else "Belief Stability",
        "20 fixed seeds; steady-state excludes each track's first 15 observations; cold start is 1-based first correct observation across all tracks/seeds. Adaptation: 30 old + 100 new frames. Burst: L=1..20 at confidence 0.9, fresh established track per L, including recovery.",
        "Labels match scripted truth; adapt to a sustained relabel.",
        f"seeds={list(seeds) if frames is None else 'custom stream'}; cold_start_samples={cold}; frames_until_switch={switch}.",
        score,
        tuple(metrics),
    )
