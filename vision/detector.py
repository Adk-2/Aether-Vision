"""YOLO-backed object inference for Project Aether frames."""

from typing import Any

from camera import Frame

from .exceptions import InferenceError
from .model import DEFAULT_MODEL_PATH, ModelLoader


class VisionDetector:
    """Run YOLO inference on canonical Frame objects."""

    def __init__(
        self,
        model_path: str = DEFAULT_MODEL_PATH,
        model_loader: ModelLoader | None = None,
    ) -> None:
        """Initialize the detector with a lazy-loading model cache."""
        self._model_loader = model_loader or ModelLoader(model_path)

    def detect(self, frame: Frame) -> Any:
        """Run inference for a frame and return the raw YOLO results."""
        model = self._model_loader.load(self._create_yolo_model)
        try:
            return model.predict(source=frame.image, verbose=False)
        except Exception as error:
            raise InferenceError(
                f"Inference failed for frame {frame.frame_id}"
            ) from error

    @staticmethod
    def _create_yolo_model(model_path: str) -> Any:
        """Create a YOLO model while keeping Ultralytics isolated here."""
        from ultralytics import YOLO

        return YOLO(model_path)
