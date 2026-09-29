import json

import cv2
import numpy as np
import pytest

from evaluation import label_video


def make_video(path, frame_count=5):
    writer = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*"MJPG"), 10.0, (16, 12))
    assert writer.isOpened()
    for value in range(frame_count):
        writer.write(np.full((12, 16, 3), value * 20, dtype=np.uint8))
    writer.release()


def test_extracts_every_nth_frame_and_empty_truth_template(tmp_path):
    video = tmp_path / "desk.avi"
    make_video(video)

    labels_path, count = label_video.extract(video, 2)
    payload = json.loads(labels_path.read_text(encoding="utf-8"))

    assert count == 3
    assert labels_path.parent == tmp_path / "desk_labels"
    assert [frame["frame_index"] for frame in payload["frames"]] == [0, 2, 4]
    assert [frame["image"] for frame in payload["frames"]] == [
        "frame_000000.jpg",
        "frame_000002.jpg",
        "frame_000004.jpg",
    ]
    assert all(frame["visible_objects"] == [] for frame in payload["frames"])
    assert all(frame["events"] == [] for frame in payload["frames"])
    assert payload["source_frame_count"] == 5
    assert payload["every_n_frames"] == 2
    assert payload["annotation_status"] == "unlabeled"
    assert len(list(labels_path.parent.glob("*.jpg"))) == 3


def test_does_not_overwrite_hand_labels(tmp_path):
    video = tmp_path / "desk.avi"
    make_video(video, 1)
    labels_path, _ = label_video.extract(video, 1)
    labels_path.write_text('{"hand_labeled": true}\n', encoding="utf-8")

    with pytest.raises(FileExistsError, match="Refusing to overwrite"):
        label_video.extract(video, 1)

    assert json.loads(labels_path.read_text(encoding="utf-8"))["hand_labeled"]


@pytest.mark.parametrize("interval", [0, -1])
def test_rejects_invalid_sampling_interval(tmp_path, interval):
    with pytest.raises(ValueError, match="greater than zero"):
        label_video.extract(tmp_path / "missing.avi", interval)


def test_rejects_missing_video(tmp_path):
    with pytest.raises(ValueError, match="Cannot open video"):
        label_video.extract(tmp_path / "missing.avi", 1)
