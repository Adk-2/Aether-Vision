"""Storage for the current scene's spatial relations."""

from .exceptions import RelationError
from .relation import Relation


class SceneGraph:
    """Store spatial relations for one current scene."""

    def __init__(self, relations: list[Relation] | None = None) -> None:
        self._relations: list[Relation] = []
        for relation in relations or []:
            self.add(relation)

    def add(self, relation: Relation) -> None:
        """Add a relation after validating its endpoints."""
        if relation.subject_track_id == relation.object_track_id:
            raise RelationError("A track cannot have a relation with itself")
        self._relations.append(relation)

    def clear(self) -> None:
        """Remove every relation."""
        self._relations.clear()

    def all_relations(self) -> list[Relation]:
        """Return a detached list of all current relations."""
        return list(self._relations)

    def get_all_relations(self) -> list[Relation]:
        """Return all relations using an explicit accessor name."""
        return self.all_relations()

    def relations_for(self, track_id: int) -> list[Relation]:
        """Return relations in which the track is either endpoint."""
        return [
            relation
            for relation in self._relations
            if track_id in (relation.subject_track_id, relation.object_track_id)
        ]

    def get_relations_for(self, track_id: int) -> list[Relation]:
        """Return all relations involving a track."""
        return self.relations_for(track_id)

    def relations_between(self, first_id: int, second_id: int) -> list[Relation]:
        """Return relations connecting two tracks in either direction."""
        endpoints = {first_id, second_id}
        return [
            relation
            for relation in self._relations
            if {relation.subject_track_id, relation.object_track_id} == endpoints
        ]

    def get_relations_between(
        self,
        first_id: int,
        second_id: int,
    ) -> list[Relation]:
        """Return all relations connecting two tracks."""
        return self.relations_between(first_id, second_id)
