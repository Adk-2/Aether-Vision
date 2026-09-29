"""Extract annotation frames without running any model inference."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


SCHEMA_VERSION = 1


def label_directory(video_path: Path) -> Path:
    """Return the sibling directory used for frames and labels."""
    return video_path.with_name(f"{video_path.stem}_labels")


def extract(video: str | Path, every_n_frames: int) -> tuple[Path, int]:
    """Extract every Nth frame and create an empty annotation template."""
    if every_n_frames <= 0:
        raise ValueError("--every-n-frames must be greater than zero")

    video_path = Path(video).resolve()
    output_dir = label_directory(video_path)
    labels_path = output_dir / "labels.json"
    if labels_path.exists():
        raise FileExistsError(
            f"Refusing to overwrite existing annotations: {labels_path}"
        )

    try:
        import cv2
    except ImportError as exc:
        raise RuntimeError("OpenCV is required for video labeling") from exc

    capture = cv2.VideoCapture(str(video_path))
    if not capture.isOpened():
        capture.release()
        raise ValueError(f"Cannot open video: {video_path}")

    output_dir.mkdir(parents=True, exist_ok=True)
    source_fps = float(capture.get(cv2.CAP_PROP_FPS))
    labeled_frames: list[dict[str, object]] = []
    decoded_count = 0
    try:
        while True:
            ok, image = capture.read()
            if not ok:
                break
            frame_index = decoded_count
            decoded_count += 1
            if frame_index % every_n_frames:
                continue
            filename = f"frame_{frame_index:06d}.jpg"
            if not cv2.imwrite(str(output_dir / filename), image):
                raise OSError(f"Could not write extracted frame: {filename}")
            timestamp = frame_index / source_fps if source_fps > 0 else None
            labeled_frames.append(
                {
                    "frame_index": frame_index,
                    "timestamp_seconds": timestamp,
                    "image": filename,
                    "visible_objects": [],
                    "events": [],
                }
            )
    finally:
        capture.release()

    if decoded_count == 0:
        raise ValueError(f"Video yielded zero frames: {video_path}")

    template = {
        "schema_version": SCHEMA_VERSION,
        "annotation_status": "unlabeled",
        "video": video_path.name,
        "source_frame_count": decoded_count,
        "source_fps": source_fps if source_fps > 0 else None,
        "every_n_frames": every_n_frames,
        "annotation_schema": {
            "visible_objects": {
                "tag": "consistent physical-object tag, e.g. phone_1",
                "class": "phone, wallet, or bottle",
                "center": ["x_pixels", "y_pixels"],
            },
            "events": {
                "tag": "same physical-object tag",
                "event": "appeared|moved|stopped|disappeared|none",
            },
        },
        "frames": labeled_frames,
    }
    labels_path.write_text(
        json.dumps(template, indent=2) + "\n",
        encoding="utf-8",
    )
    return labels_path, len(labeled_frames)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Extract frames and create an empty real-video label template."
    )
    parser.add_argument("--video", required=True)
    parser.add_argument("--every-n-frames", required=True, type=int)
    args = parser.parse_args()
    labels_path, count = extract(args.video, args.every_n_frames)
    print(f"Extracted {count} frames")
    print(f"Labels template: {labels_path}")
    print("No model predictions were run or written.")


if __name__ == "__main__":
    main()
