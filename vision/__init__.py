"""Canonical vision interfaces for Project Aether."""

from .adapters import DetectionAdapter
from .detection import Detection
from .detector import VisionDetector
from .exceptions import InferenceError, ModelLoadError, VisionError
from .model import DEFAULT_MODEL_PATH, ModelLoader
from .renderer import Renderer

__all__ = [
    "DEFAULT_MODEL_PATH",
    "Detection",
    "DetectionAdapter",
    "InferenceError",
    "ModelLoadError",
    "ModelLoader",
    "Renderer",
    "VisionDetector",
    "VisionError",
]
