"""Independent deterministic inference rules."""

from abc import ABC, abstractmethod

from .inference import Inference
from .inference_result import InferenceResult


class Rule(ABC):
    """Define the interface implemented by every inference rule."""

    @abstractmethod
    def applies(self, knowledge: Inference) -> bool:
        """Return whether this rule's conditions are satisfied."""

    @abstractmethod
    def infer(self, knowledge: Inference) -> InferenceResult:
        """Return the explainable conclusion produced by this rule."""


class StationaryObjectRule(Rule):
    """Infer that a stationary object remains at its last location."""

    confidence = 0.90

    def applies(self, knowledge: Inference) -> bool:
        return knowledge.current_state == "STATIC" and not knowledge.recent_movement

    def infer(self, knowledge: Inference) -> InferenceResult:
        return InferenceResult(
            success=True,
            conclusion=(
                f"{knowledge.object_name} is probably still where it was "
                "last observed."
            ),
            confidence=self.confidence,
            supporting_facts=["STATIC", "No recent movement"],
            triggered_rules=[type(self).__name__],
            timestamp=knowledge.timestamp,
        )


class NearbyRelationshipRule(Rule):
    """Infer explicit nearby relationships from the scene graph."""

    confidence = 0.95

    def applies(self, knowledge: Inference) -> bool:
        return bool(knowledge.nearby_objects)

    def infer(self, knowledge: Inference) -> InferenceResult:
        nearby = ", ".join(knowledge.nearby_objects)
        return InferenceResult(
            success=True,
            conclusion=f"{knowledge.object_name} is near {nearby}.",
            confidence=self.confidence,
            supporting_facts=[
                f"Near {object_name}" for object_name in knowledge.nearby_objects
            ],
            triggered_rules=[type(self).__name__],
            timestamp=knowledge.timestamp,
        )


class RecentlyMovedRule(Rule):
    """Infer that the latest unresolved movement transition is recent."""

    confidence = 0.85

    def applies(self, knowledge: Inference) -> bool:
        return knowledge.recent_movement

    def infer(self, knowledge: Inference) -> InferenceResult:
        movement_facts = [
            event
            for event in knowledge.recent_events
            if event in {"MOVED", "STARTED_MOVING"}
        ]
        return InferenceResult(
            success=True,
            conclusion=f"{knowledge.object_name} was recently moved.",
            confidence=self.confidence,
            supporting_facts=movement_facts[-1:] or ["Recent movement"],
            triggered_rules=[type(self).__name__],
            timestamp=knowledge.timestamp,
        )
