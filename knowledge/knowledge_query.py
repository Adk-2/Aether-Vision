"""Lightweight structured query helpers."""

from .exceptions import KnowledgeQueryError
from .knowledge_engine import KnowledgeEngine
from .knowledge_result import KnowledgeResult
from .query_types import QueryType


class KnowledgeQuery:
    """Provide a small pure-Python interface to KnowledgeEngine."""

    def __init__(self, engine: KnowledgeEngine) -> None:
        self._engine = engine

    def query(self, query_type: QueryType, name: str) -> KnowledgeResult:
        handlers = {
            QueryType.WHERE_IS: self.where_is,
            QueryType.WHAT_HAPPENED: self.what_happened,
            QueryType.OBJECTS_NEAR: self.objects_near,
            QueryType.CURRENT_BELIEF: self.current_belief,
            QueryType.CURRENT_STATE: self.current_state,
        }
        try:
            handler = handlers[query_type]
        except (KeyError, TypeError) as error:
            raise KnowledgeQueryError(f"Unsupported query type: {query_type!r}") from error
        return handler(name)

    def where_is(self, name: str) -> KnowledgeResult:
        return self._engine.where_is(name)

    def what_happened(self, name: str) -> KnowledgeResult:
        return self._engine.what_happened(name)

    def objects_near(self, name: str) -> KnowledgeResult:
        return self._engine.objects_near(name)

    def current_belief(self, name: str) -> KnowledgeResult:
        return self._engine.current_belief(name)

    def current_state(self, name: str) -> KnowledgeResult:
        return self._engine.current_state(name)


def where_is(engine: KnowledgeEngine, name: str) -> KnowledgeResult:
    """Query an object's latest location."""
    return engine.where_is(name)


def what_happened(engine: KnowledgeEngine, name: str) -> KnowledgeResult:
    """Query an object's event history."""
    return engine.what_happened(name)


def objects_near(engine: KnowledgeEngine, name: str) -> KnowledgeResult:
    """Query objects currently near an object."""
    return engine.objects_near(name)


def current_belief(engine: KnowledgeEngine, name: str) -> KnowledgeResult:
    """Query an object's stable belief."""
    return engine.current_belief(name)


def current_state(engine: KnowledgeEngine, name: str) -> KnowledgeResult:
    """Query an object's current memory state."""
    return engine.current_state(name)
