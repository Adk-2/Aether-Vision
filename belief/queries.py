"""Convenience queries for stable beliefs."""

from .belief_engine import BeliefEngine
from .belief_state import BeliefState
from .exceptions import BeliefNotFoundError


def belief(engine: BeliefEngine, track_id: int) -> BeliefState:
    """Return a belief or raise when its track is unknown."""
    state = engine.get(track_id)
    if state is None:
        raise BeliefNotFoundError(f"Unknown track ID: {track_id}")
    return state


def current_belief(engine: BeliefEngine, track_id: int) -> str:
    """Return the current stable belief for a track."""
    return belief(engine, track_id).current_belief


def alternatives(engine: BeliefEngine, track_id: int) -> list[tuple[str, float]]:
    """Return alternatives ordered by descending confidence then label."""
    items = belief(engine, track_id).alternative_beliefs.items()
    return sorted(items, key=lambda item: (-item[1], item[0]))
