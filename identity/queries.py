"""Convenience queries for resolved identities."""

from .exceptions import IdentityNotFoundError
from .identity import Identity
from .resolver import IdentityResolver

DEFAULT_ALTERNATIVE_LIMIT = 3


def identity(resolver: IdentityResolver, track_id: int) -> Identity:
    """Return a resolved identity or raise when it is unknown."""
    resolved = resolver.get(track_id)
    if resolved is None:
        raise IdentityNotFoundError(f"Unknown track ID: {track_id}")
    return resolved


def current_label(resolver: IdentityResolver, track_id: int) -> str:
    """Return the stabilized label for a track."""
    return identity(resolver, track_id).current_label


def top_alternatives(
    resolver: IdentityResolver,
    track_id: int,
    limit: int = DEFAULT_ALTERNATIVE_LIMIT,
) -> list[tuple[str, float]]:
    """Return alternative labels with normalized confidence shares."""
    resolved = identity(resolver, track_id)
    alternatives = [
        (label, resolved.history.normalized_confidence(label))
        for label, _ in resolved.history.top_labels(limit + 1)
        if label != resolved.current_label
    ]
    return alternatives[:limit]
