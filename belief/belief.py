"""Public belief model."""

from .belief_state import BeliefState

# Belief is the public domain name; BeliefState emphasizes its mutable lifecycle.
Belief = BeliefState

__all__ = ["Belief", "BeliefState"]
