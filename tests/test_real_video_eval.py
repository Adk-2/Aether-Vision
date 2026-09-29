import json
from types import SimpleNamespace
from unittest.mock import patch

import numpy as np
import pytest

from belief import BeliefEngine
from camera import Frame
from events import EventEngine, EventFilter
from evaluation import real_video_eval as real_eval
from identity import IdentityResolver
from tracking import Tracker
from vision import ConfidenceFilter, DetectionAdapter, DetectionStabilizer
from world import WorldState


class ScriptedDetector:
    def __init__(self, centers, classes=None):
        self.centers = centers
        self.classes = classes or ["bottle"] * len(centers)

    def detect(self, frame):
        center = self.centers[frame.frame_id]
        class_name = self.classes[frame.frame_id]
        x, y = center
        box = SimpleNamespace(
            cls=[0],
            conf=[0.9],
            xyxy=[(x - 5, y - 5, x + 5, y + 5)],
        )
        return [SimpleNamespace(names={0: class_name}, boxes=[box])]


def components(centers, classes=None):
    return real_eval.PipelineComponents(
        detector=ScriptedDetector(centers, classes),
        adapter=DetectionAdapter(),
        confidence_filter=ConfidenceFilter(),
        tracker=Tracker(),
        stabilizer=DetectionStabilizer(),
        identity=IdentityResolver(),
        belief=BeliefEngine(),
        world=WorldState(),
        event_engine=EventEngine(),
        event_filter=EventFilter(),
    )


def frames(count):
    from datetime import datetime, timedelta

    return [
        Frame(
            frame_id=index,
            image=np.zeros((20, 20, 3), dtype=np.uint8),
            timestamp=datetime(2026, 1, 1) + timedelta(milliseconds=33 * index),
            width=20,
            height=20,
            channels=3,
        )
        for index in range(count)
    ]


def write_labels(path, centers, *, status="complete", events=None):
    event_names = events or ["none"] * len(centers)
    payload = {
        "schema_version": 1,
        "annotation_status": status,
        "video": "desk.mp4",
        "frames": [
            {
                "frame_index": index,
                "visible_objects": [
                    {"tag": "bottle_1", "class": "bottle", "center": list(center)}
                ],
                "events": [{"tag": "bottle_1", "event": event_names[index]}],
            }
            for index, center in enumerate(centers)
        ],
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload


def test_incomplete_ground_truth_stops_before_detector_construction(tmp_path):
    labels = tmp_path / "labels.json"
    write_labels(labels, [(10, 10)], status="unlabeled")
    with patch.object(
        real_eval,
        "default_components",
        side_effect=AssertionError("detector constructed"),
    ):
        with pytest.raises(ValueError, match="not complete"):
            real_eval.evaluate(tmp_path / "desk.mp4", labels)


def test_real_chain_scores_objects_identity_events_and_timings(tmp_path):
    centers = [(10, 10), *[(20, 10)] * 6]
    labels = tmp_path / "labels.json"
    write_labels(
        labels,
        centers,
        events=["appeared", "moved", "none", "none", "stopped", "none", "none"],
    )

    result = real_eval.evaluate(
        tmp_path / "desk.mp4",
        labels,
        components=components(centers),
        frames=frames(7),
    )

    assert vars(result.detection) == {
        "true_positive": 7,
        "false_positive": 0,
        "false_negative": 0,
    }
    assert (result.identity_correct, result.identity_total) == (7, 7)
    assert result.track_switches == 0
    assert vars(result.events) == {
        "true_positive": 3,
        "false_positive": 0,
        "false_negative": 0,
    }
    assert result.failures == []
    assert len(result.frame_durations) == 2
    assert all(len(samples) == 2 for samples in result.stage_samples.values())
    assert set(result.stage_samples) == {
        "detector",
        "adapter",
        "confidence filter",
        "tracker",
        "stabilizer",
        "identity",
        "belief",
        "world + apply beliefs",
        "event engine",
        "event filter",
    }


def test_reports_track_switch_and_concrete_event_mismatches(tmp_path):
    truth_centers = [(10, 10), *[(100, 10)] * 6]
    labels = tmp_path / "labels.json"
    write_labels(
        labels,
        truth_centers,
        events=["appeared", "moved", "none", "none", "none", "none", "none"],
    )

    result = real_eval.evaluate(
        tmp_path / "desk.mp4",
        labels,
        components=components(truth_centers),
        frames=frames(7),
    )
    report = real_eval.render_report([result])

    assert result.track_switches == 1
    assert any(
        item.kind == "track ID switch"
        and item.frame_index == 1
        and "track 0 -> 1" in item.detail
        for item in result.failures
    )
    assert any(item.kind == "missed filtered event" for item in result.failures)
    assert "## Notable failures" in report
    assert "track 0 -> 1" in report
    assert "interval ending here expected moved" in report


def test_detection_class_error_is_both_false_positive_and_false_negative(tmp_path):
    centers = [(10, 10)] * 7
    labels = tmp_path / "labels.json"
    write_labels(labels, centers, events=["appeared", *["none"] * 6])
    classes = ["bottle"] * 6 + ["cup"]

    result = real_eval.evaluate(
        tmp_path / "desk.mp4",
        labels,
        components=components(centers, classes),
        frames=frames(7),
    )

    assert result.detection.true_positive == 6
    assert result.detection.false_positive == 1
    assert result.detection.false_negative == 1
    assert any(
        item.frame_index == 6 and item.kind == "wrong detection class"
        for item in result.failures
    )


def test_sparse_event_label_closes_prior_interval(tmp_path):
    centers = [(10, 10), *[(20, 10)] * 6]
    labels = tmp_path / "labels.json"
    payload = write_labels(labels, [centers[0], centers[-1]])
    payload["frames"][1]["frame_index"] = 6
    payload["frames"][0]["events"][0]["event"] = "appeared"
    payload["frames"][1]["events"] = [
        {"tag": "bottle_1", "event": "moved"},
        {"tag": "bottle_1", "event": "stopped"},
    ]
    labels.write_text(json.dumps(payload), encoding="utf-8")

    result = real_eval.evaluate(
        tmp_path / "desk.mp4",
        labels,
        components=components(centers),
        frames=frames(7),
    )

    assert result.events.true_positive == 3
    assert result.events.false_positive == result.events.false_negative == 0


def test_nearest_center_matching_is_one_to_one():
    matches, missing, extra = real_eval.nearest_matches(
        [(0, 0), (10, 0)], [(1, 0), (9, 0), (100, 0)], 5
    )
    assert [(a, b) for a, b, _ in matches] == [(0, 0), (1, 1)]
    assert missing == []
    assert extra == [2]


def test_label_validation_requires_complete_per_object_events(tmp_path):
    labels = tmp_path / "labels.json"
    payload = write_labels(labels, [(10, 10)])
    payload["frames"][0]["events"] = []
    labels.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError, match="no event/none label"):
        real_eval.load_labels(labels, tmp_path / "desk.mp4")


@pytest.mark.parametrize("event", ["moved", "stopped", "none"])
def test_nonvisible_non_disappearance_event_is_rejected(tmp_path, event):
    labels = tmp_path / "labels.json"
    payload = write_labels(labels, [(10, 10), (10, 10)])
    payload["frames"][1]["visible_objects"] = []
    payload["frames"][1]["events"] = [{"tag": "bottle_1", "event": event}]
    labels.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError, match="is not visible"):
        real_eval.load_labels(labels, tmp_path / "desk.mp4")


def test_labels_digest_is_captured_before_evaluation(tmp_path):
    labels = tmp_path / "labels.json"
    write_labels(labels, [(10, 10)])
    loaded = real_eval.load_labels(labels, tmp_path / "desk.mp4")
    from hashlib import sha256

    assert loaded.digest == sha256(labels.read_bytes()).hexdigest()
