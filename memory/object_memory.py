"""In-memory storage for tracked objects."""

from .schemas import TrackedObject


class ObjectMemory:
    """Store and retrieve tracked objects by their unique identifiers."""

    def __init__(self) -> None:
        """Initialize an empty object store."""
        self._objects: dict[str, TrackedObject] = {}

    def add_object(self, tracked_object: TrackedObject) -> None:
        """Add an object or replace the object with the same identifier."""
        self._objects[tracked_object.object_id] = tracked_object

    def get_object(self, object_id: str) -> TrackedObject | None:
        """Return the object with the given identifier, if it exists."""
        return self._objects.get(object_id)

    def remove_object(self, object_id: str) -> TrackedObject | None:
        """Remove and return an object, or return None if it does not exist."""
        return self._objects.pop(object_id, None)

    def get_all_objects(self) -> list[TrackedObject]:
        """Return a list containing all currently stored objects."""
        return list(self._objects.values())

    def count(self) -> int:
        """Return the number of currently stored objects."""
        return len(self._objects)
