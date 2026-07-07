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


class OcclusionRule(Rule):
    """Explain an unexplained disappearance using nearby visible objects."""

    confidence = 0.75

    def applies(self, knowledge: Inference) -> bool:
        return (
            knowledge.recently_disappeared
            and bool(knowledge.nearby_objects)
            and not knowledge.removal_evidence
        )

    def infer(self, knowledge: Inference) -> InferenceResult:
        return InferenceResult(
            success=True,
            conclusion=f"{knowledge.object_name} is probably occluded.",
            confidence=self.confidence,
            supporting_facts=[
                "Recently disappeared",
                *[f"{name} nearby" for name in knowledge.nearby_objects],
                "No removal evidence",
            ],
            triggered_rules=[type(self).__name__],
            timestamp=knowledge.timestamp,
        )


class CarryAwayRule(Rule):
    """Explain a disappearance when a nearby person moved away."""

    confidence = 0.80

    def applies(self, knowledge: Inference) -> bool:
        return (
            knowledge.recently_disappeared
            and bool(knowledge.nearby_people)
            and bool(knowledge.people_recently_moved_away)
        )

    def infer(self, knowledge: Inference) -> InferenceResult:
        person = knowledge.people_recently_moved_away[0]
        return InferenceResult(
            success=True,
            conclusion=f"{knowledge.object_name} was probably carried away.",
            confidence=self.confidence,
            supporting_facts=[
                "Recently disappeared",
                f"{person} nearby",
                f"{person} recently moved away",
            ],
            triggered_rules=[type(self).__name__],
            timestamp=knowledge.timestamp,
        )


class ObjectPermanenceRule(Rule):
    """Preserve existence when disappearance has no terminal explanation."""

    confidence = 0.90

    def applies(self, knowledge: Inference) -> bool:
        return (
            knowledge.recently_disappeared
            and not knowledge.removal_evidence
            and not knowledge.destruction_evidence
        )

    def infer(self, knowledge: Inference) -> InferenceResult:
        return InferenceResult(
            success=True,
            conclusion=(
                f"{knowledge.object_name} probably still exists outside "
                "the current camera view."
            ),
            confidence=self.confidence,
            supporting_facts=[
                "Recently disappeared",
                "No removal evidence",
                "No destruction evidence",
            ],
            triggered_rules=[type(self).__name__],
            timestamp=knowledge.timestamp,
        )
