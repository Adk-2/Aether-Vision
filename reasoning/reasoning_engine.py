"""Orchestration of deterministic rule evaluation."""

from dataclasses import replace
from datetime import datetime

from knowledge import KnowledgeEngine

from .inference import Inference
from .inference_result import InferenceResult
from .rule_registry import RuleRegistry

MOVEMENT_STARTED_EVENTS = {"MOVED", "STARTED_MOVING"}
MOVEMENT_STOPPED_EVENTS = {"STOPPED", "STOPPED_MOVING"}
DISAPPEARANCE_EVENTS = {"DISAPPEARED"}
REMOVAL_EVENTS = {"REMOVED", "TAKEN", "PICKED_UP"}
DESTRUCTION_EVENTS = {"DESTROYED", "BROKEN"}
PERSON_LABELS = {"person", "people", "man", "woman", "boy", "girl"}


class ReasoningEngine:
    """Collect knowledge facts and evaluate every registered rule."""

    def __init__(
        self,
        knowledge_engine: KnowledgeEngine,
        rule_registry: RuleRegistry,
    ) -> None:
        self._knowledge_engine = knowledge_engine
        self._rule_registry = rule_registry
        self._nearby_history: dict[str, list[str]] = {}

    def observe(self, object_names: list[str]) -> None:
        """Retain the last visible neighbourhood for later disappearance queries."""
        for object_name in object_names:
            nearby = self._knowledge_engine.objects_near(object_name)
            if nearby.success:
                self._nearby_history[object_name] = list(nearby.result)

    def infer(self, object_name: str) -> list[InferenceResult]:
        """Return every rule conclusion that applies to an object."""
        facts = self._collect_facts(object_name)
        results: list[InferenceResult] = []
        evaluated_rules: set[int] = set()
        while True:
            added_result = False
            working_facts = replace(
                facts,
                inferred_conclusions=[result.conclusion for result in results],
            )
            for rule in self._rule_registry.all_rules():
                rule_identity = id(rule)
                if rule_identity in evaluated_rules or not rule.applies(working_facts):
                    continue
                results.append(rule.infer(working_facts))
                evaluated_rules.add(rule_identity)
                added_result = True
            if not added_result:
                break
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
        recently_disappeared = (
            (state.success and state.result.value == "LOST")
            or bool(DISAPPEARANCE_EVENTS.intersection(event_names))
        )
        raw_nearby = list(nearby.result) if nearby.success else []
        if recently_disappeared and not raw_nearby:
            raw_nearby = self._nearby_history.get(
                state.object_name if state.success else object_name,
                [],
            )
        nearby_people = [name for name in raw_nearby if self._is_person(name)]
        moved_people = [
            name for name in nearby_people if self._object_recently_moved(name)
        ]
        return Inference(
            object_name=resolved_name,
            current_state=state.result.value if state.success else None,
            location=location.result if location.success else None,
            nearby_objects=[self._display_name(name) for name in raw_nearby],
            recent_events=event_names,
            recent_movement=self._has_unresolved_movement(event_names),
            recently_disappeared=recently_disappeared,
            removal_evidence=bool(REMOVAL_EVENTS.intersection(event_names)),
            destruction_evidence=bool(DESTRUCTION_EVENTS.intersection(event_names)),
            nearby_people=[self._display_name(name) for name in nearby_people],
            people_recently_moved_away=[
                self._display_name(name) for name in moved_people
            ],
            timestamp=timestamp,
        )

    def _object_recently_moved(self, object_name: str) -> bool:
        history = self._knowledge_engine.what_happened(object_name)
        if not history.success:
            return False
        names = [entry.event_type.name for entry in history.result]
        return self._has_unresolved_movement(names)

    @classmethod
    def _is_person(cls, object_name: str) -> bool:
        return cls._display_name(object_name).casefold() in PERSON_LABELS

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
