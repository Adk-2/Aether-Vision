"""Evaluation contracts requested in Phase 2c; no policy expectations are tuned."""

from dataclasses import replace
from unittest.mock import patch
import pytest
from evaluation import Score, Measurement
from evaluation.evaluator import Evaluator
from evaluation.metrics import Average, Percentage
from evaluation.report import EvaluationReport
from evaluation.scenarios import (
    event_quality,
    identity_stability,
    belief_stability,
    query_accuracy,
)
from evaluation.scenarios.common import noisy_multitrack_stream, relabel_stream
from evaluation.scenarios.label_quality import burst_tolerance, SEEDS
from evaluation import perf
from events import EventType
from assistant import QuerySource


def metric(result, label):
    return next(m for m in result.metrics if m.label == label)


@pytest.mark.parametrize(
    "args",
    [(0.5, 1, 3), (0, 0, 0), (1, -1, -1), (0.5, 1, None), (0.5, None, 2), (1, 2, 1)],
)
def test_score_rejects_inconsistent_counts(args):
    with pytest.raises(ValueError):
        Score(*args)


@pytest.mark.parametrize(
    "call",
    [
        lambda: Average(0, 0).value,
        lambda: Percentage(0, 0).value,
        lambda: Evaluator([]),
        lambda: EvaluationReport([]),
        lambda: perf._percentile([], 50),
        lambda: perf.run(frame_count=0),
    ],
)
def test_empty_aggregations_are_not_zero(call):
    with pytest.raises(ValueError):
        call()


def test_raw_event_oracle_retains_jitter_and_frame8_stop():
    frames = event_quality.scripted_frames()
    assert (1, EventType.STOPPED) in frames[8].expected_events
    for frame in frames:
        if frame.jitter_only:
            assert all(kind is not EventType.MOVED for _, kind in frame.expected_events)


def test_pipeline_oracle_and_mismatches():
    result = event_quality.run_pipeline()
    assert "(1, 1, 'STARTED_MOVING', 'predicted')" in result.actual_result
    assert "(3, 1, 'STARTED_MOVING', 'missed')" in result.actual_result
    frames = event_quality.pipeline_frames()
    corrupted = [
        replace(f, expected_events=((99, EventType.APPEARED),)) for f in frames
    ]
    other = event_quality.evaluate(corrupted, pipeline=True)
    for label in ("precision tp/(tp+fp)", "recall tp/(tp+fn)", "F1"):
        assert metric(result, label).value != metric(other, label).value


@pytest.mark.parametrize("pipeline", [False, True])
def test_jitter_frame_truth_controls_jitter_metric(pipeline):
    frames = (
        event_quality.pipeline_frames() if pipeline else event_quality.scripted_frames()
    )
    baseline = event_quality.evaluate(frames, pipeline=pipeline)
    # Jitter membership is its ground truth, not the expected-event multiset.
    corrupt = [replace(f, jitter_only=i == 0) for i, f in enumerate(frames)]
    changed = event_quality.evaluate(corrupt, pipeline=pipeline)
    assert (
        metric(baseline, "jitter false-movement rate").value
        != metric(changed, "jitter false-movement rate").value
    )


@pytest.mark.parametrize("scenario", [identity_stability, belief_stability])
def test_each_label_measurement_responds_to_truth(scenario):
    frames = noisy_multitrack_stream()
    corrupted = [
        replace(
            f,
            observations=tuple(
                replace(o, expected_label="wrong") for o in f.observations
            ),
        )
        for f in frames
    ]
    baseline, changed = (
        scenario.evaluate(frames=frames),
        scenario.evaluate(frames=corrupted),
    )
    for label in (
        "steady-state pooled accuracy",
        "steady-state accuracy mean",
        "steady-state accuracy min",
        "steady-state accuracy max",
        "cold start mean",
        "cold start min",
        "cold start max",
    ):
        assert metric(baseline, label).value != metric(changed, label).value
    adaptation = relabel_stream()
    corrupted = [
        replace(
            f,
            observations=tuple(
                replace(o, expected_label="wrong") for o in f.observations
            ),
        )
        for f in adaptation
    ]
    changed = scenario.evaluate(adaptation_frames=corrupted)
    assert metric(changed, "frames until switch").value == ">100"
    assert metric(baseline, "frames until switch").value != ">100"
    assert isinstance(metric(baseline, "frames until switch"), Measurement)
    assert len(SEEDS) == 20
    assert scenario.evaluate(seeds=SEEDS) == scenario.evaluate(seeds=SEEDS)


def test_burst_truth_sensitivity():
    assert burst_tolerance() != burst_tolerance(expected_label="wrong")


def test_query_intents_have_varied_states_and_wrong_counts_are_sensitive():
    cases = query_accuracy.supported_cases()
    for intent in (
        "WHERE_IS",
        "WHERE_WAS",
        "LAST_SEEN",
        "VISIBILITY",
        "CURRENT_OBJECTS",
        "RECENT_HISTORY",
    ):
        assert {c.state for c in cases if c.intent == intent} >= {
            "visible",
            "lost",
            "never",
            "two",
            "moved",
        }
    baseline = query_accuracy.evaluate()
    corrupted = [replace(c, expected_text="WRONG") for c in cases]
    changed = query_accuracy.evaluate(supported=corrupted)
    assert (
        metric(changed, "supported confidently wrong answers").numerator
        > metric(baseline, "supported confidently wrong answers").numerator
    )
    # The stock paraphrases all abstain. Include a supported phrasing in this set
    # to verify a confident answer is checked against its independent oracle.
    phrase = query_accuracy.QueryCase(
        "probe", "where is the phone", QuerySource.CURRENT, "(10, 20)"
    )
    baseline = query_accuracy.evaluate(paraphrases=[phrase])
    changed = query_accuracy.evaluate(
        paraphrases=[replace(phrase, expected_text="WRONG")]
    )
    assert metric(baseline, "paraphrases confidently wrong answers").numerator == 0
    assert metric(changed, "paraphrases confidently wrong answers").numerator == 1


def test_reports_have_no_aggregate_score_or_duplicate_footer():
    report = Evaluator().run()
    text = report.to_console_text()
    assert "Overall Score" not in text
    assert text.count("\n==============================================") == 1
    assert "'predicted'" in report.to_markdown()


def test_synthetic_never_calls_detector_and_omits_fps():
    with patch.object(
        perf.VisionDetector, "detect", side_effect=AssertionError("detector called")
    ):
        text = perf.run(frame_count=8)
    assert "SYNTHETIC: detector not run, FPS not representative" in text
    assert "mean FPS" not in text and "FPS excluding" not in text
    assert "| detector |" not in text
    assert "warm-up discarded: 5; measured: 3" in text


def test_invalid_and_empty_video(tmp_path):
    with pytest.raises(ValueError, match="Cannot open"):
        perf.run(str(tmp_path / "missing.avi"))
    with patch("cv2.VideoCapture") as capture:
        capture.return_value.isOpened.return_value = True
        capture.return_value.read.return_value = (False, None)
        with pytest.raises(ValueError, match="zero frames"):
            perf.run("empty.avi")
        capture.return_value.release.assert_called_once()


def test_video_uses_real_stage_chain_and_excludes_warmup():
    from types import SimpleNamespace

    order, samples = [], []

    def stage(name, original):
        def wrapped(*args, **kwargs):
            order.append(name)
            return original(*args, **kwargs)

        return wrapped

    targets = [
        (perf.DetectionAdapter, "convert"),
        (perf.ConfidenceFilter, "filter"),
        (perf.Tracker, "update"),
        (perf.DetectionStabilizer, "stabilize"),
        (perf.IdentityResolver, "update"),
        (perf.BeliefEngine, "update"),
        (perf.EventEngine, "generate_events"),
        (perf.EventFilter, "filter_events"),
        (perf.QueryEngine, "answer"),
    ]
    from contextlib import ExitStack

    with ExitStack() as stack:
        stack.enter_context(
            patch.object(
                perf, "_load_video_frames", return_value=perf._synthetic_frames(8)
            )
        )
        detector = stack.enter_context(patch.object(perf, "VisionDetector"))
        detector.return_value.detect.side_effect = lambda frame: (
            order.append("detect") or []
        )
        detector.return_value._model_loader.load.return_value = SimpleNamespace(
            predictor=SimpleNamespace(imgsz=[640, 640])
        )
        for cls, name in targets:
            stack.enter_context(
                patch.object(cls, name, stage(name, getattr(cls, name)))
            )
        original = perf.StageTimings.add

        def add(self, name, seconds):
            samples.append(name)
            original(self, name, seconds)

        stack.enter_context(patch.object(perf.StageTimings, "add", add))
        text = perf.run("fixture.avi", 8)
    assert (
        order
        == [
            "detect",
            "convert",
            "filter",
            "update",
            "stabilize",
            "update",
            "update",
            "generate_events",
            "filter_events",
            "answer",
        ]
        * 8
    )
    assert samples.count("detector") == 3
    assert all(samples.count(name) == 3 for name in set(samples))
    assert "End-to-end mean FPS:" in text
    assert "FPS excluding detector:" in text
