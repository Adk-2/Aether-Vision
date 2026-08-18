"""Build readable assistant responses from existing engine results."""

from knowledge import KnowledgeResult
from knowledge.knowledge_engine import CURRENT_SOURCE
from planning import Plan
from reasoning import InferenceResult

from .formatter import Formatter


class ResponseBuilder:
    """Convert deterministic subsystem outputs into terminal responses."""

    def __init__(self, formatter: Formatter | None = None) -> None:
        self._formatter = formatter or Formatter()

    def unknown(self) -> str:
        return (
            "I can answer: where is, what happened to, what is near, "
            "or how do I find an object."
        )

    def not_found(self, object_name: str) -> str:
        return self._formatter.sections([
            ("Object", self._formatter.display_name(object_name)),
            ("Answer", "I do not have that object in current memory."),
        ])

    def where_is(
        self,
        knowledge: KnowledgeResult,
        reasoning: list[InferenceResult],
        plan: Plan,
    ) -> str:
        if not knowledge.success:
            return self.not_found(knowledge.object_name)
        location_label = (
            "Current Observation"
            if CURRENT_SOURCE in knowledge.source_modules
            else "Last Known Observation"
        )
        location_text = self._location_sentence(knowledge)
        return self._formatter.sections([
            ("Object", self._formatter.display_name(knowledge.object_name)),
            (location_label, location_text),
            ("Timestamp", self._formatter.timestamp(knowledge.timestamp)),
            ("Reasoning", self._reasoning_lines(reasoning)),
            ("Plan", self._plan_lines(plan)),
        ])

    def what_happened(
        self,
        knowledge: KnowledgeResult,
        reasoning: list[InferenceResult],
    ) -> str:
        if not knowledge.success:
            return self.not_found(knowledge.object_name)
        events = [entry.description for entry in knowledge.result[-5:]]
        return self._formatter.sections([
            ("Object", self._formatter.display_name(knowledge.object_name)),
            ("Recent Events", events),
            ("Reasoning", self._reasoning_lines(reasoning)),
        ])

    def what_is_near(self, knowledge: KnowledgeResult) -> str:
        if not knowledge.success:
            return self.not_found(knowledge.object_name)
        nearby = [
            self._formatter.display_name(object_name)
            for object_name in knowledge.result
        ]
        return self._formatter.sections([
            ("Object", self._formatter.display_name(knowledge.object_name)),
            ("Nearby", nearby),
            ("Timestamp", self._formatter.timestamp(knowledge.timestamp)),
        ])

    def how_to_find(
        self,
        knowledge: KnowledgeResult,
        reasoning: list[InferenceResult],
        plan: Plan,
    ) -> str:
        if not knowledge.success:
            return self.not_found(knowledge.object_name)
        location_label = (
            "Current Observation"
            if CURRENT_SOURCE in knowledge.source_modules
            else "Last Known Observation"
        )
        return self._formatter.sections([
            ("Object", self._formatter.display_name(knowledge.object_name)),
            (location_label, self._location_sentence(knowledge)),
            ("Reasoning", self._reasoning_lines(reasoning)),
            ("Plan", self._plan_lines(plan)),
        ])

    def _location_sentence(self, knowledge: KnowledgeResult) -> str:
        name = self._formatter.display_name(knowledge.object_name)
        location = self._formatter.value(knowledge.result)
        if CURRENT_SOURCE in knowledge.source_modules:
            return f"{name} is currently observed at {location}."
        timestamp = self._formatter.timestamp(knowledge.timestamp)
        return f"{name} was last observed at {location} at {timestamp}."

    @staticmethod
    def _reasoning_lines(results: list[InferenceResult]) -> list[str]:
        return [result.conclusion for result in results]

    @staticmethod
    def _plan_lines(plan: Plan) -> list[str]:
        return [action.description for action in plan.actions]
