"""Adapters from model-specific results to canonical detections."""

from datetime import datetime
from typing import Any
from uuid import uuid4

from .detection import Detection

BOUNDING_BOX_COORDINATE_COUNT = 4


class DetectionAdapter:
    """Convert raw inference results into Detection objects."""

    def convert(
        self,
        raw_results: Any,
        timestamp: datetime,
    ) -> list[Detection]:
        """Convert every result box without filtering or rendering."""
        detections: list[Detection] = []
        for result in raw_results:
            boxes = getattr(result, "boxes", None)
            if boxes is None:
                continue
            for box in boxes:
                detections.append(self._convert_box(box, result.names, timestamp))
        return detections

    @staticmethod
    def _convert_box(
        box: Any,
        class_names: Any,
        timestamp: datetime,
    ) -> Detection:
        """Convert one raw result box into a Detection."""
        class_id = int(DetectionAdapter._first_scalar(box.cls))
        confidence = float(DetectionAdapter._first_scalar(box.conf))
        coordinates = DetectionAdapter._first_vector(box.xyxy)
        if len(coordinates) != BOUNDING_BOX_COORDINATE_COUNT:
            raise ValueError("A detection bounding box must have four coordinates")

        x_min, y_min, x_max, y_max = (
            int(coordinate) for coordinate in coordinates
        )
        bounding_box = (x_min, y_min, x_max, y_max)
        center = ((x_min + x_max) // 2, (y_min + y_max) // 2)
        return Detection(
            detection_id=str(uuid4()),
            class_id=class_id,
            class_name=str(class_names[class_id]),
            confidence=confidence,
            bounding_box=bounding_box,
            center=center,
            timestamp=timestamp,
        )

    @staticmethod
    def _first_scalar(values: Any) -> Any:
        """Extract a Python scalar from the first tensor-like value."""
        value = values[0]
        return value.item() if hasattr(value, "item") else value

    @staticmethod
    def _first_vector(values: Any) -> list[float]:
        """Extract a Python coordinate vector from tensor-like values."""
        value = values[0]
        coordinates = value.tolist() if hasattr(value, "tolist") else value
        return list(coordinates)
