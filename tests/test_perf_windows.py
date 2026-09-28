from unittest.mock import patch
import numpy as np
import pytest
from evaluation import perf


def test_first_and_last_windows_exclude_middle_and_warmup():
    samples = [0.001] * 200 + [99] * 10 + [0.003] * 200
    text = "\n".join(perf.window_report(samples, [10] * 410, [2] * 410))
    assert "first 200: 6-205 | 1.0000" in text
    assert "last 200: 216-415 | 3.0000" in text
    assert "n/a" in "".join(perf.window_report([1] * 399, [1] * 399, [1] * 399))


def test_video_streaming_replay_is_explicit_and_timestamps_increase():
    image = np.zeros((2, 2, 3), dtype=np.uint8)
    with patch("cv2.VideoCapture") as capture:
        capture.return_value.read.side_effect = [(True, image), (False, None)]
        assert len(list(perf._load_video_frames("clip", 3))) == 1
        capture.return_value.set.assert_not_called()
        capture.return_value.release.assert_called_once()
    with patch("cv2.VideoCapture") as capture:
        capture.return_value.read.side_effect = [
            (True, image),
            (False, None),
            (True, image),
            (True, image),
        ]
        frames = list(perf._load_video_frames("clip", 3, loop_video=True))
        assert len(frames) == 3
        assert frames[0].timestamp < frames[1].timestamp < frames[2].timestamp
        capture.return_value.set.assert_called_once()
        capture.return_value.release.assert_called_once()


def test_short_video_and_loop_without_video_are_rejected():
    with patch.object(
        perf, "_load_video_frames", return_value=perf._synthetic_frames(5)
    ):
        with pytest.raises(ValueError, match="warm-up"):
            perf.run("short.avi", 2000)
    with pytest.raises(ValueError, match="requires"):
        perf.run(loop_video=True)
