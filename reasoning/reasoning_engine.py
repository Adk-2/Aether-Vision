"""Orchestration of deterministic rule evaluation."""

from datetime import datetime

from knowledge import KnowledgeEngine

from .inference import Inference
from .inference_result import InferenceResult
from .rule_registry import RuleRegistry

MOVEMENT_STARTED_EVENTS = {"MOVED", "STARTED_MOVING"}
MOVEMENT_STOPPED_EVENTS = {"STOPPED", "STOPPED_MOVING"}


class ReasoningEngine:
    """Collect knowledge facts and evaluate every registered rule."""

    def __init__(
        self,
        knowledge_engine: KnowledgeEngine,
        rule_registry: RuleRegistry,
    ) -> None:
        self._knowledge_engine = knowledge_engine
        self._rule_registry = rule_registry

    def infer(self, object_name: str) -> list[InferenceResult]:
        """Return every rule conclusion that applies to an object."""
        facts = self._collect_facts(object_name)
        results: list[InferenceResult] = []
        for rule in self._rule_registry.all_rules():
            if rule.applies(facts):
                results.append(rule.infer(facts))
        return results

    def _collect_facts(self, object_name: str) -> Inference:
        state = self._knowledge_engine.current_state(object_name)
        location = self._knowledge_engine.where_is(object_name)
        nearby = self._knowledge_engine.objects_near(object_name)
        history = self._knowledge_engine.what_happened(object_name)
        event_names = (
            [entry.event_type.name for entry in history.result]
            if history.success
            else []
        )
        timestamp = self._latest_timestamp(
            state.timestamp,
            location.timestamp,
            nearby.timestamp,
            history.timestamp,
        )
        resolved_name = self._display_name(
            state.object_name if state.success else object_name
        )
        return Inference(
            object_name=resolved_name,
            current_state=state.result.value if state.success else None,
            location=location.result if location.success else None,
            nearby_objects=(
                [self._display_name(name) for name in nearby.result]
                if nearby.success
                else []
            ),
            recent_events=event_names,
            recent_movement=self._has_unresolved_movement(event_names),
            timestamp=timestamp,
        )

    @staticmethod
    def _has_unresolved_movement(event_names: list[str]) -> bool:
        for event_name in reversed(event_names):
            if event_name in MOVEMENT_STOPPED_EVENTS:
                return False
            if event_name in MOVEMENT_STARTED_EVENTS:
                return True
        return False

    @staticmethod
    def _latest_timestamp(*timestamps: datetime | None) -> datetime | None:
        available = [timestamp for timestamp in timestamps if timestamp is not None]
        return max(available) if available else None

    @staticmethod
    def _display_name(object_name: str) -> str:
        label, separator, suffix = object_name.rpartition("_")
        return label if separator and suffix.isdigit() else object_name
