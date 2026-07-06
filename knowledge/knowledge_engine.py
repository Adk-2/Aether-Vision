"""Unified orchestration over Project Aether knowledge sources."""

from datetime import datetime

from belief import BeliefEngine
from memory import MemoryEngine, MemoryRecord
from scene import RelationType, SceneGraph
from timeline import Timeline

from .knowledge_result import KnowledgeResult
from .query_types import QueryType

MEMORY_SOURCE = "WorkingMemory"
TIMELINE_SOURCE = "Timeline"
SCENE_SOURCE = "SceneGraph"
BELIEF_SOURCE = "BeliefEngine"


class KnowledgeEngine:
    """Query existing knowledge sources without owning their data."""

    def __init__(
        self,
        working_memory: MemoryEngine,
        timeline: Timeline,
        scene_graph: SceneGraph,
        belief_engine: BeliefEngine,
    ) -> None:
        self._working_memory = working_memory
        self._timeline = timeline
        self._scene_graph = scene_graph
        self._belief_engine = belief_engine

    def use_scene_graph(self, scene_graph: SceneGraph) -> None:
        """Point queries at the pipeline's latest graph without copying it."""
        self._scene_graph = scene_graph

    def where_is(self, name: str) -> KnowledgeResult:
        record = self._resolve(name)
        if record is None:
            return self._not_found(QueryType.WHERE_IS, name, [MEMORY_SOURCE])
        return self._success(
            QueryType.WHERE_IS,
            record,
            record.last_position,
            record.last_seen,
            [MEMORY_SOURCE],
        )

    def what_happened(self, name: str) -> KnowledgeResult:
        record = self._resolve(name)
        if record is None:
            return self._not_found(
                QueryType.WHAT_HAPPENED,
                name,
                [MEMORY_SOURCE, TIMELINE_SOURCE],
            )
        entries = self._timeline.store.entries_for_track(record.track_id)
        timestamp = entries[-1].timestamp if entries else record.last_seen
        return self._success(
            QueryType.WHAT_HAPPENED,
            record,
            entries,
            timestamp,
            [MEMORY_SOURCE, TIMELINE_SOURCE],
        )

    def objects_near(self, name: str) -> KnowledgeResult:
        record = self._resolve(name)
        if record is None:
            return self._not_found(
                QueryType.OBJECTS_NEAR,
                name,
                [MEMORY_SOURCE, SCENE_SOURCE],
            )
        relations = [
            relation
            for relation in self._scene_graph.all_relations()
            if relation.subject_track_id == record.track_id
            and relation.relation_type is RelationType.NEAR
        ]
        nearby = [relation.object_name for relation in relations]
        timestamp = max(
            (relation.timestamp for relation in relations),
            default=record.last_seen,
        )
        return self._success(
            QueryType.OBJECTS_NEAR,
            record,
            nearby,
            timestamp,
            [MEMORY_SOURCE, SCENE_SOURCE],
        )

    def current_belief(self, name: str) -> KnowledgeResult:
        record = self._resolve(name)
        if record is None:
            return self._not_found(
                QueryType.CURRENT_BELIEF,
                name,
                [MEMORY_SOURCE, BELIEF_SOURCE],
            )
        state = self._belief_engine.get(record.track_id)
        if state is None:
            return self._not_found(
                QueryType.CURRENT_BELIEF,
                record.object_name,
                [MEMORY_SOURCE, BELIEF_SOURCE],
            )
        return self._success(
            QueryType.CURRENT_BELIEF,
            record,
            state.current_belief,
            state.stable_since,
            [MEMORY_SOURCE, BELIEF_SOURCE],
            state.confidence,
        )

    def current_state(self, name: str) -> KnowledgeResult:
        record = self._resolve(name)
        if record is None:
            return self._not_found(QueryType.CURRENT_STATE, name, [MEMORY_SOURCE])
        return self._success(
            QueryType.CURRENT_STATE,
            record,
            record.status,
            record.last_seen,
            [MEMORY_SOURCE],
        )

    def _resolve(self, name: str) -> MemoryRecord | None:
        query = name.strip().casefold()
        if not query:
            return None
        exact = self._working_memory.store.get_by_name(name.strip())
        if exact is not None:
            return exact
        matches = [
            record
            for record in self._working_memory.store.list_all()
            if self._label(record.object_name).casefold() == query
        ]
        return matches[0] if len(matches) == 1 else None

    @staticmethod
    def _label(object_name: str) -> str:
        label, separator, suffix = object_name.rpartition("_")
        return label if separator and suffix.isdigit() else object_name

    @staticmethod
    def _success(
        query_type: QueryType,
        record: MemoryRecord,
        result: object,
        timestamp: datetime | None,
        sources: list[str],
        confidence: float | None = None,
    ) -> KnowledgeResult:
        return KnowledgeResult(
            success=True,
            query_type=query_type,
            object_name=record.object_name,
            result=result,
            confidence=confidence,
            timestamp=timestamp,
            source_modules=sources,
        )

    @staticmethod
    def _not_found(
        query_type: QueryType,
        name: str,
        sources: list[str],
    ) -> KnowledgeResult:
        return KnowledgeResult(
            success=False,
            query_type=query_type,
            object_name=name,
            result=None,
            confidence=None,
            timestamp=None,
            source_modules=sources,
        )
