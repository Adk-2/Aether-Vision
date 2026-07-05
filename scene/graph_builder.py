"""Build scene graphs using only track geometry."""

from itertools import combinations
from math import hypot

from tracking import Track

from .exceptions import SceneGraphError
from .graph import SceneGraph
from .relation import Relation
from .relation_types import RelationType

DEFAULT_NEAR_DISTANCE = 150.0
MINIMUM_NEAR_DISTANCE = 0.0
TRACK_ID_WIDTH = 3


class SceneGraphBuilder:
    """Derive spatial relations from active tracks."""

    def __init__(self, near_distance: float = DEFAULT_NEAR_DISTANCE) -> None:
        if near_distance < MINIMUM_NEAR_DISTANCE:
            raise SceneGraphError("Near distance cannot be negative")
        self._near_distance = near_distance

    def build(self, tracks: list[Track]) -> SceneGraph:
        """Return a new graph containing relations among active tracks."""
        active_tracks = [track for track in tracks if track.active]
        track_ids = [track.track_id for track in active_tracks]
        if len(track_ids) != len(set(track_ids)):
            raise SceneGraphError("Active tracks must have unique identifiers")

        graph = SceneGraph()
        for first, second in combinations(active_tracks, 2):
            self._add_pair_relations(graph, first, second)
        return graph

    def _add_pair_relations(
        self,
        graph: SceneGraph,
        first: Track,
        second: Track,
    ) -> None:
        first_x, first_y = first.current_detection.center
        second_x, second_y = second.current_detection.center

        if first_x < second_x:
            self._add_inverse(graph, first, second, RelationType.LEFT_OF, RelationType.RIGHT_OF)
        elif first_x > second_x:
            self._add_inverse(graph, first, second, RelationType.RIGHT_OF, RelationType.LEFT_OF)

        if first_y < second_y:
            self._add_inverse(graph, first, second, RelationType.ABOVE, RelationType.BELOW)
        elif first_y > second_y:
            self._add_inverse(graph, first, second, RelationType.BELOW, RelationType.ABOVE)

        if hypot(second_x - first_x, second_y - first_y) <= self._near_distance:
            self._add_symmetric(graph, first, second, RelationType.NEAR)
        if self._overlaps(first, second):
            self._add_symmetric(graph, first, second, RelationType.OVERLAPS)

    def _add_inverse(
        self,
        graph: SceneGraph,
        first: Track,
        second: Track,
        forward: RelationType,
        reverse: RelationType,
    ) -> None:
        graph.add(self._relation(first, second, forward))
        graph.add(self._relation(second, first, reverse))

    def _add_symmetric(
        self,
        graph: SceneGraph,
        first: Track,
        second: Track,
        relation_type: RelationType,
    ) -> None:
        self._add_inverse(graph, first, second, relation_type, relation_type)

    @staticmethod
    def _overlaps(first: Track, second: Track) -> bool:
        first_left, first_top, first_right, first_bottom = first.current_detection.bounding_box
        second_left, second_top, second_right, second_bottom = second.current_detection.bounding_box
        return (
            first_left < second_right
            and first_right > second_left
            and first_top < second_bottom
            and first_bottom > second_top
        )

    @staticmethod
    def _relation(subject: Track, object_: Track, relation_type: RelationType) -> Relation:
        return Relation(
            subject_track_id=subject.track_id,
            object_track_id=object_.track_id,
            subject_name=SceneGraphBuilder._name(subject),
            object_name=SceneGraphBuilder._name(object_),
            relation_type=relation_type,
            timestamp=max(subject.last_seen, object_.last_seen),
        )

    @staticmethod
    def _name(track: Track) -> str:
        label = track.stabilized_label or track.current_detection.class_name
        return f"{label}_{track.track_id:0{TRACK_ID_WIDTH}d}"
