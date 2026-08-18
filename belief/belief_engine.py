"""Belief lifecycle management."""

from identity import Identity

from .belief_policy import BeliefPolicy
from .belief_state import BeliefState
from .exceptions import BeliefError


class BeliefEngine:
    """Maintain one stable belief per observed track."""

    def __init__(self, policy: BeliefPolicy | None = None) -> None:
        self._policy = policy or BeliefPolicy()
        self._beliefs: dict[int, BeliefState] = {}

    def update(self, identities: list[Identity]) -> list[BeliefState]:
        """Update beliefs from the current frame's identities."""
        track_ids = [identity.track_id for identity in identities]
        if len(track_ids) != len(set(track_ids)):
            raise BeliefError("Identities must have unique track identifiers")
        observed_track_ids = set(track_ids)
        for track_id, state in self._beliefs.items():
            if track_id not in observed_track_ids:
                self._policy.decay(state)
        updated = []
        for identity in identities:
            state = self._beliefs.get(identity.track_id)
            if state is None:
                state = self._create(identity)
                self._beliefs[identity.track_id] = state
            else:
                self._policy.apply(state, identity)
            updated.append(state)
        return updated

    def get(self, track_id: int) -> BeliefState | None:
        """Return a belief, or None if its track has not been observed."""
        return self._beliefs.get(track_id)

    def all(self) -> list[BeliefState]:
        """Return beliefs in first-observed order."""
        return list(self._beliefs.values())

    def replace_all(self, states: list[BeliefState]) -> None:
        """Replace belief state from a trusted serialized snapshot."""
        self._beliefs = {state.track_id: state for state in states}

    @staticmethod
    def _create(identity: Identity) -> BeliefState:
        return BeliefState(
            track_id=identity.track_id,
            current_belief=identity.current_label,
            confidence=identity.confidence,
            stable_since=identity.last_updated,
            frames_stable=1,
        )
