"""Conservative belief stabilization for resolved identities."""

from .belief import Belief
from .belief_engine import BeliefEngine
from .belief_policy import (
    BELIEF_DECAY,
    MIN_CONFIDENCE_MARGIN,
    MIN_CONSECUTIVE_OBSERVATIONS,
    BeliefPolicy,
)
from .belief_state import BeliefState
from .exceptions import BeliefError, BeliefNotFoundError
from .queries import alternatives, belief, current_belief

__all__ = [
    "BELIEF_DECAY", "MIN_CONFIDENCE_MARGIN", "MIN_CONSECUTIVE_OBSERVATIONS",
    "Belief", "BeliefEngine", "BeliefError", "BeliefNotFoundError",
    "BeliefPolicy", "BeliefState", "alternatives", "belief", "current_belief",
]
