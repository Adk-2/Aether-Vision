"""Deterministic planner that consumes knowledge, reasoning, and goals."""

from datetime import datetime

from knowledge import KnowledgeEngine
from reasoning import ReasoningEngine

from .goal import Goal
from .plan import Plan
from .planner_rules import (
    NO_EVIDENCE_CONFIDENCE,
    USEFUL_EVIDENCE_CONFIDENCE,
    PlanningContext,
    PlannerRules,
    build_context,
)


class Planner:
    """Choose explainable actions for a goal without executing them."""

    def __init__(
        self,
        knowledge_engine: KnowledgeEngine,
        reasoning_engine: ReasoningEngine,
        planner_rules: PlannerRules,
    ) -> None:
        self._knowledge_engine = knowledge_engine
        self._reasoning_engine = reasoning_engine
        self._planner_rules = planner_rules

    def create_plan(self, goal: Goal) -> Plan:
        """Return a deterministic plan for the supplied goal."""
        context = build_context(goal, self._knowledge_engine, self._reasoning_engine)
        actions = [
            rule.propose(context)
            for rule in self._planner_rules.all_rules()
            if rule.applies(context)
        ]
        actions.sort(key=lambda action: action.priority, reverse=True)
        return Plan(
            goal=goal,
            actions=actions,
            confidence=self._confidence(context, actions),
            generated_time=datetime.now(),
        )

    @staticmethod
    def _confidence(context: PlanningContext, actions: list[object]) -> float:
        if not actions:
            return 0.0
        confidences = [
            result.confidence
            for result in context.reasoning_results
            if getattr(result, "confidence", None) is not None
        ]
        if not confidences:
            return (
                USEFUL_EVIDENCE_CONFIDENCE
                if context.has_useful_evidence
                else NO_EVIDENCE_CONFIDENCE
            )
        return max(confidences)
