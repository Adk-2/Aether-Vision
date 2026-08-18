"""Rule-based parsing for assistant queries."""

from dataclasses import dataclass
import re

from .intent import Intent

OPTIONAL_MY = r"(?:my\s+)?"
OBJECT_PATTERN = r"(?P<object>[a-zA-Z][a-zA-Z0-9_-]*(?:\s+[a-zA-Z0-9_-]+)*)"
QUERY_PATTERNS: tuple[tuple[Intent, re.Pattern[str]], ...] = (
    (
        Intent.WHERE_IS,
        re.compile(rf"^where\s+is\s+{OPTIONAL_MY}{OBJECT_PATTERN}\??$", re.I),
    ),
    (
        Intent.WHAT_HAPPENED,
        re.compile(
            rf"^what\s+happened\s+to\s+{OPTIONAL_MY}{OBJECT_PATTERN}\??$",
            re.I,
        ),
    ),
    (
        Intent.WHAT_IS_NEAR,
        re.compile(rf"^what\s+is\s+near\s+{OPTIONAL_MY}{OBJECT_PATTERN}\??$", re.I),
    ),
    (
        Intent.HOW_TO_FIND,
        re.compile(
            rf"^how\s+do\s+i\s+find\s+{OPTIONAL_MY}{OBJECT_PATTERN}\??$",
            re.I,
        ),
    ),
)


@dataclass(frozen=True)
class ParsedQuery:
    """Structured result of deterministic query parsing."""

    intent: Intent
    object_name: str | None = None


class QueryHandler:
    """Parse supported natural-language query shapes without AI."""

    def parse(self, query: str) -> ParsedQuery:
        """Return a parsed query or UNKNOWN for unsupported text."""
        normalized = " ".join(query.strip().split())
        if not normalized:
            return ParsedQuery(Intent.UNKNOWN)
        for intent, pattern in QUERY_PATTERNS:
            match = pattern.match(normalized)
            if match is None:
                continue
            return ParsedQuery(intent, self._normalize_object(match.group("object")))
        return ParsedQuery(Intent.UNKNOWN)

    @staticmethod
    def _normalize_object(object_name: str) -> str:
        return object_name.strip().casefold()
