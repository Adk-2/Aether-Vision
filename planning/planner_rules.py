"""Deterministic planner rules."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from knowledge import KnowledgeEngine
from reasoning import InferenceResult, ReasoningEngine

from .action import Action
from .goal import Goal

KNOWN_LOCATION_PRIORITY = 100
NEARBY_SEARCH_PRIORITY = 90
EXPAND_SEARCH_PRIORITY = 10
USEFUL_EVIDENCE_CONFIDENCE = 0.70
NO_EVIDENCE_CONFIDENCE = 0.30


@dataclass(frozen=True)
class PlanningContext:
    """Facts available to planner rules for one goal."""

    goal: Goal
    display_name: str
    known_location: object | None = None
    nearby_objects: list[str] = field(default_factory=list)
    reasoning_results: list[InferenceResult] = field(default_factory=list)

    @property
    def has_useful_evidence(self) -> bool:
        """Return whether the planner has a concrete search lead."""
        return self.known_location is not None or bool(self.nearby_objects)


class PlannerRule(ABC):
    """Interface implemented by every deterministic planner rule."""

    @abstractmethod
    def applies(self, context: PlanningContext) -> bool:
        """Return whether the rule can propose an action."""

    @abstractmethod
    def propose(self, context: PlanningContext) -> Action:
        """Return the action proposed by this rule."""


class FindObjectRule(PlannerRule):
    """Recommend checking the object's known location first."""

    def applies(self, context: PlanningContext) -> bool:
        return context.known_location is not None

    def propose(self, context: PlanningContext) -> Action:
        return Action(
            description=f"Inspect last known location {context.known_location}.",
            priority=KNOWN_LOCATION_PRIORITY,
            reason=f"{context.display_name} last observed there.",
        )


class SearchNearbyRule(PlannerRule):
    """Recommend checking objects that are or were near the target."""

    def applies(self, context: PlanningContext) -> bool:
        return bool(context.nearby_objects)

    def propose(self, context: PlanningContext) -> Action:
        nearby = context.nearby_objects[0]
        return Action(
            description=f"Search near {nearby}.",
            priority=NEARBY_SEARCH_PRIORITY,
            reason=f"{context.display_name} probably remained beside {nearby}.",
        )


class ExpandSearchRule(PlannerRule):
    """Recommend expanding the search when no concrete lead exists."""

    def applies(self, context: PlanningContext) -> bool:
        return not context.has_useful_evidence

    def propose(self, context: PlanningContext) -> Action:
        return Action(
            description="Expand search area.",
            priority=EXPAND_SEARCH_PRIORITY,
            reason="No useful location or nearby-object evidence exists.",
        )


class PlannerRules:
    """Own the deterministic planner rule set."""

    def __init__(self, rules: list[PlannerRule] | None = None) -> None:
        self._rules = [
            FindObjectRule(),
            SearchNearbyRule(),
            ExpandSearchRule(),
        ] if rules is None else rules

    def all_rules(self) -> list[PlannerRule]:
        """Return registered planner rules in deterministic order."""
        return list(self._rules)


def build_context(
    goal: Goal,
    knowledge_engine: KnowledgeEngine,
    reasoning_engine: ReasoningEngine,
) -> PlanningContext:
    """Collect planning facts from knowledge and reasoning."""
    location = knowledge_engine.where_is(goal.target_object)
    nearby = knowledge_engine.objects_near(goal.target_object)
    reasoning_results = reasoning_engine.infer(goal.target_object)
    known_location = location.result if location.success else None
    nearby_objects = list(nearby.result) if nearby.success and nearby.result else []
    nearby_objects.extend(_nearby_from_reasoning(reasoning_results))
    return PlanningContext(
        goal=goal,
        display_name=_display_name(location.object_name),
        known_location=known_location,
        nearby_objects=_unique_display_names(nearby_objects),
        reasoning_results=reasoning_results,
    )


def _nearby_from_reasoning(results: list[InferenceResult]) -> list[str]:
    nearby: list[str] = []
    for result in results:
        for fact in result.supporting_facts:
            normalized = fact.strip()
            lowered = normalized.casefold()
            if lowered.startswith("near "):
                nearby.append(normalized[5:])
            elif lowered.endswith(" nearby"):
                nearby.append(normalized[:-7])
    return nearby


def _unique_display_names(object_names: list[str]) -> list[str]:
    return list(dict.fromkeys(_display_name(name) for name in object_names))


def _display_name(object_name: str) -> str:
    label, separator, suffix = object_name.rpartition("_")
    return label if separator and suffix.isdigit() else object_name
