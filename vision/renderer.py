"""OpenCV rendering for Project Aether tracks."""

from typing import TYPE_CHECKING

import cv2

from camera import Frame

if TYPE_CHECKING:
    from tracking import Track

WINDOW_TITLE = "Project Aether"
QUIT_KEY = "q"
MEMORY_KEY = "m"
TIMELINE_KEY = "t"
SCENE_GRAPH_KEY = "g"
IDENTITY_KEY = "i"
BELIEF_KEY = "b"
FRAME_DELAY_MILLISECONDS = 1
KEY_CODE_MASK = 0xFF
BOUNDING_BOX_COLOR = (0, 255, 0)
TEXT_COLOR = (255, 255, 255)
TEXT_BACKGROUND_COLOR = (0, 0, 0)
LINE_THICKNESS = 2
TEXT_THICKNESS = 1
FONT_SCALE = 0.5
LABEL_PADDING = 4
FPS_POSITION = (10, 30)
FPS_FONT_SCALE = 0.8
FPS_LABEL = "FPS"
FPS_DECIMAL_PLACES = 1
CONFIDENCE_DECIMAL_PLACES = 2
TRACK_ID_LABEL = "ID"


class Renderer:
    """Draw and display tracked detections without performing inference."""

    def __init__(self) -> None:
        self.memory_requested = False
        self.timeline_requested = False
        self.scene_graph_requested = False
        self.identity_requested = False
        self.belief_requested = False

    def render(
        self,
        frame: Frame,
        tracks: list["Track"],
        fps: float,
    ) -> bool:
        """Display an annotated frame and return whether Q was pressed."""
        image = frame.image.copy()
        for track in tracks:
            self._draw_track(image, track)
        self._draw_fps(image, fps)
        cv2.imshow(WINDOW_TITLE, image)
        key = cv2.waitKey(FRAME_DELAY_MILLISECONDS) & KEY_CODE_MASK
        self.memory_requested = key == ord(MEMORY_KEY)
        self.timeline_requested = key == ord(TIMELINE_KEY)
        self.scene_graph_requested = key == ord(SCENE_GRAPH_KEY)
        self.identity_requested = key == ord(IDENTITY_KEY)
        self.belief_requested = key == ord(BELIEF_KEY)
        return key == ord(QUIT_KEY)

    @staticmethod
    def _draw_track(image: object, track: "Track") -> None:
        """Draw one tracked detection box and its identity label."""
        detection = track.current_detection
        x_min, y_min, x_max, y_max = detection.bounding_box
        cv2.rectangle(
            image,
            (x_min, y_min),
            (x_max, y_max),
            BOUNDING_BOX_COLOR,
            LINE_THICKNESS,
        )
        object_label = track.stabilized_label or detection.class_name
        confidence = (
            track.identity_confidence
            if track.identity_confidence is not None
            else detection.confidence
        )
        label = (
            f"{TRACK_ID_LABEL} {track.track_id} | "
            f"{object_label} "
            f"{confidence:.{CONFIDENCE_DECIMAL_PLACES}f}"
        )
        Renderer._draw_label(image, label, x_min, y_min)

    @staticmethod
    def _draw_label(image: object, label: str, x: int, y: int) -> None:
        """Draw a readable text label above a detection box."""
        font = cv2.FONT_HERSHEY_SIMPLEX
        (text_width, text_height), baseline = cv2.getTextSize(
            label,
            font,
            FONT_SCALE,
            TEXT_THICKNESS,
        )
        label_bottom = max(y, text_height + baseline + LABEL_PADDING)
        label_top = label_bottom - text_height - baseline - LABEL_PADDING
        cv2.rectangle(
            image,
            (x, label_top),
            (x + text_width + LABEL_PADDING, label_bottom),
            TEXT_BACKGROUND_COLOR,
            cv2.FILLED,
        )
        cv2.putText(
            image,
            label,
            (x + LABEL_PADDING // 2, label_bottom - baseline),
            font,
            FONT_SCALE,
            TEXT_COLOR,
            TEXT_THICKNESS,
            cv2.LINE_AA,
        )

    @staticmethod
    def _draw_fps(image: object, fps: float) -> None:
        """Draw the supplied frame rate on an image."""
        cv2.putText(
            image,
            f"{FPS_LABEL}: {fps:.{FPS_DECIMAL_PLACES}f}",
            FPS_POSITION,
            cv2.FONT_HERSHEY_SIMPLEX,
            FPS_FONT_SCALE,
            TEXT_COLOR,
            LINE_THICKNESS,
            cv2.LINE_AA,
        )

    @staticmethod
    def close() -> None:
        """Close all windows created by the renderer."""
        cv2.destroyAllWindows()
