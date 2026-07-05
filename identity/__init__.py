"""Deterministic tracked-object identity stabilization."""

from .confidence_fusion import ConfidenceFusion
from .exceptions import IdentityError, IdentityNotFoundError
from .identity import Identity
from .label_history import LabelHistory
from .queries import current_label, identity, top_alternatives
from .resolver import IdentityResolver

__all__ = [
    "ConfidenceFusion",
    "Identity",
    "IdentityError",
    "IdentityNotFoundError",
    "IdentityResolver",
    "LabelHistory",
    "current_label",
    "identity",
    "top_alternatives",
]
