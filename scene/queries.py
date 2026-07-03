"""Convenience queries for scene graphs."""

from .graph import SceneGraph
from .relation import Relation
from .relation_types import RelationType


class SceneQueries:
    """Provide object-oriented queries over a scene graph."""

    def __init__(self, graph: SceneGraph) -> None:
        self._graph = graph

    def relations_for(self, track_id: int) -> list[Relation]:
        return self._graph.relations_for(track_id)

    def objects_left_of(self, track_id: int) -> list[int]:
        return self._objects(track_id, RelationType.LEFT_OF)

    def objects_right_of(self, track_id: int) -> list[int]:
        return self._objects(track_id, RelationType.RIGHT_OF)

    def objects_near(self, track_id: int) -> list[int]:
        return self._objects(track_id, RelationType.NEAR)

    def _objects(self, track_id: int, relation_type: RelationType) -> list[int]:
        return [
            relation.object_track_id
            for relation in self._graph.all_relations()
            if relation.subject_track_id == track_id
            and relation.relation_type is relation_type
        ]


def relations_for(graph: SceneGraph, track_id: int) -> list[Relation]:
    return SceneQueries(graph).relations_for(track_id)


def objects_left_of(graph: SceneGraph, track_id: int) -> list[int]:
    return SceneQueries(graph).objects_left_of(track_id)


def objects_right_of(graph: SceneGraph, track_id: int) -> list[int]:
    return SceneQueries(graph).objects_right_of(track_id)


def objects_near(graph: SceneGraph, track_id: int) -> list[int]:
    return SceneQueries(graph).objects_near(track_id)
