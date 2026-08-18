"""Supported deterministic assistant intents."""

from enum import Enum


class Intent(Enum):
    """Classify the assistant query patterns Project Aether supports."""

    WHERE_IS = "WHERE_IS"
    WHAT_HAPPENED = "WHAT_HAPPENED"
    WHAT_IS_NEAR = "WHAT_IS_NEAR"
    HOW_TO_FIND = "HOW_TO_FIND"
    UNKNOWN = "UNKNOWN"
