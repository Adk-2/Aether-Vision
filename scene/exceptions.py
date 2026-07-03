"""Scene graph exceptions."""


class SceneGraphError(Exception):
    """Base exception for invalid scene graph operations."""


class RelationError(SceneGraphError):
    """Raised when a relation is invalid."""
