"""Model loading and caching for the vision subsystem."""

from collections.abc import Callable
from typing import Any

from .exceptions import ModelLoadError

DEFAULT_MODEL_PATH = "yolov8n.pt"


class ModelLoader:
    """Load and cache one model for a configurable model path."""

    def __init__(self, model_path: str = DEFAULT_MODEL_PATH) -> None:
        """Initialize a loader without loading the model immediately."""
        self._model_path = model_path
        self._model: Any | None = None

    @property
    def model_path(self) -> str:
        """Return the currently configured model path."""
        return self._model_path

    def load(self, model_factory: Callable[[str], Any]) -> Any:
        """Load the configured model once and return the cached instance."""
        if self._model is None:
            try:
                self._model = model_factory(self._model_path)
            except Exception as error:
                raise ModelLoadError(
                    f"Unable to load vision model: {self._model_path!r}"
                ) from error
        return self._model

    def set_model_path(self, model_path: str) -> None:
        """Change the model path and clear the currently cached model."""
        if model_path == self._model_path:
            return
        self._model_path = model_path
        self._model = None
