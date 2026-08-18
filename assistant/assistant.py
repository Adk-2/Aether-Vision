"""Deterministic assistant orchestration over existing Project Aether modules."""

from datetime import datetime

from knowledge import KnowledgeEngine
from planning import Goal, Planner
from reasoning import ReasoningEngine

from .intent import Intent
from .query_handler import QueryHandler
from .response_builder import ResponseBuilder


class Assistant:
    """Answer user queries by delegating to existing deterministic engines."""

    def __init__(
        self,
        knowledge_engine: KnowledgeEngine,
        reasoning_engine: ReasoningEngine,
        planner: Planner,
        query_handler: QueryHandler | None = None,
        response_builder: ResponseBuilder | None = None,
    ) -> None:
        self._knowledge_engine = knowledge_engine
        self._reasoning_engine = reasoning_engine
        self._planner = planner
        self._query_handler = query_handler or QueryHandler()
        self._response_builder = response_builder or ResponseBuilder()

    def answer(self, query: str) -> str:
        """Parse a query, call the matching subsystem, and format the result."""
        parsed = self._query_handler.parse(query)
        object_name = parsed.object_name
        if parsed.intent is Intent.UNKNOWN or object_name is None:
            return self._response_builder.unknown()
        if parsed.intent is Intent.WHERE_IS:
            knowledge = self._knowledge_engine.where_is(object_name)
            reasoning = self._reasoning_engine.infer(object_name)
            plan = self._planner.create_plan(self._find_goal(object_name))
            return self._response_builder.where_is(knowledge, reasoning, plan)
        if parsed.intent is Intent.WHAT_HAPPENED:
            knowledge = self._knowledge_engine.what_happened(object_name)
            reasoning = self._reasoning_engine.infer(object_name)
            return self._response_builder.what_happened(knowledge, reasoning)
        if parsed.intent is Intent.WHAT_IS_NEAR:
            knowledge = self._knowledge_engine.objects_near(object_name)
            return self._response_builder.what_is_near(knowledge)
        if parsed.intent is Intent.HOW_TO_FIND:
            knowledge = self._knowledge_engine.where_is(object_name)
            reasoning = self._reasoning_engine.infer(object_name)
            plan = self._planner.create_plan(self._find_goal(object_name))
            return self._response_builder.how_to_find(knowledge, reasoning, plan)
        return self._response_builder.unknown()

    @staticmethod
    def _find_goal(object_name: str) -> Goal:
        return Goal(
            goal_type="find",
            target_object=object_name,
            priority=1,
            timestamp=datetime.now(),
        )
