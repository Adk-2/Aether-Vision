"""Deterministic rules for evolving object beliefs."""

from identity import Identity

from .belief_state import BeliefState
from .exceptions import BeliefError

MIN_CONSECUTIVE_OBSERVATIONS = 10
MIN_CONFIDENCE_MARGIN = 0.20
BELIEF_DECAY = 0.98
MIN_BELIEF_CONFIDENCE = 0.05


class BeliefPolicy:
    """Apply conservative, deterministic belief switching rules."""

    def __init__(self, belief_decay: float = BELIEF_DECAY) -> None:
        if not 0.0 <= belief_decay <= 1.0:
            raise BeliefError("Belief decay must be between zero and one")
        self._decay = belief_decay
        self._challenger_labels: dict[int, str] = {}
        self._challenger_streaks: dict[int, int] = {}

    def apply(self, state: BeliefState, observation: Identity) -> BeliefState:
        """Update a state from one identity observation and return it."""
        if state.track_id != observation.track_id:
            raise BeliefError("Belief and identity track IDs must match")
        if observation.current_label == state.current_belief:
            self._reinforce(state, observation)
        else:
            self._challenge(state, observation)
        return state

    def decay(self, state: BeliefState) -> BeliefState:
        """Decay an unobserved belief and break any challenger streak.

        Decay is applied once per frame, so confidence loss depends on FPS.
        """
        state.confidence *= self._decay
        self._decay_alternatives(state)
        self._clear_challenger(state.track_id)
        return state

    def _reinforce(self, state: BeliefState, observation: Identity) -> None:
        state.confidence = observation.confidence
        state.frames_stable += 1
        state.alternative_beliefs.pop(state.current_belief, None)
        self._clear_challenger(state.track_id)

    def _challenge(self, state: BeliefState, observation: Identity) -> None:
        label = observation.current_label
        state.confidence *= self._decay
        self._decay_alternatives(state)
        state.alternative_beliefs[label] = observation.confidence
        if self._challenger_labels.get(state.track_id) == label:
            self._challenger_streaks[state.track_id] += 1
        else:
            self._challenger_labels[state.track_id] = label
            self._challenger_streaks[state.track_id] = 1

        if self._can_switch(state, observation):
            self._switch(state, observation)
        else:
            state.frames_stable += 1

    def _can_switch(self, state: BeliefState, observation: Identity) -> bool:
        return (
            self._challenger_streaks[state.track_id]
            >= MIN_CONSECUTIVE_OBSERVATIONS
            and observation.confidence - state.confidence
            >= MIN_CONFIDENCE_MARGIN
        )

    def _switch(self, state: BeliefState, observation: Identity) -> None:
        previous_label = state.current_belief
        previous_confidence = state.confidence
        state.current_belief = observation.current_label
        state.confidence = observation.confidence
        state.stable_since = observation.last_updated
        state.frames_stable = 1
        state.alternative_beliefs.pop(observation.current_label, None)
        state.alternative_beliefs[previous_label] = previous_confidence
        self._clear_challenger(state.track_id)

    def _decay_alternatives(self, state: BeliefState) -> None:
        for label in tuple(state.alternative_beliefs):
            state.alternative_beliefs[label] *= self._decay

    def _clear_challenger(self, track_id: int) -> None:
        self._challenger_labels.pop(track_id, None)
        self._challenger_streaks.pop(track_id, None)
