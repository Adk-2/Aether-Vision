"""Small deterministic interpreter for natural-language Aether questions."""

from dataclasses import dataclass
import re
import string

from .intent import Intent

ALIASES = {
    "cellphone": "cell phone",
    "mobile": "cell phone",
    "mobile phone": "cell phone",
    "phone": "cell phone",
}

OBJECT_PATTERN = r"(?P<object>[a-z][a-z0-9]*(?:\s+[a-z0-9]+)*)"
OPTIONAL_THE = r"(?:the\s+)?"
QUERY_PATTERNS: tuple[tuple[Intent, re.Pattern[str]], ...] = (
    (Intent.CURRENT_OBJECTS, re.compile(r"^what objects do you see$")),
    (Intent.RECENT_HISTORY, re.compile(r"^what did you see earlier$")),
    (Intent.RECENT_HISTORY, re.compile(r"^what happened recently$")),
    (
        Intent.LAST_SEEN,
        re.compile(rf"^when was {OPTIONAL_THE}{OBJECT_PATTERN} last seen$"),
    ),
    (
        Intent.VISIBILITY,
        re.compile(rf"^is {OPTIONAL_THE}{OBJECT_PATTERN} visible$"),
    ),
    (
        Intent.VISIBILITY,
        re.compile(rf"^is {OPTIONAL_THE}{OBJECT_PATTERN} currently visible$"),
    ),
    (
        Intent.WHERE_WAS,
        re.compile(rf"^where was {OPTIONAL_THE}{OBJECT_PATTERN}$"),
    ),
    (
        Intent.WHERE_IS,
        re.compile(rf"^where is {OPTIONAL_THE}{OBJECT_PATTERN}$"),
    ),
)


@dataclass(frozen=True)
class ParsedQuery:
    """Structured result of deterministic query parsing."""

    intent: Intent
    object_name: str | None = None


class QueryInterpreter:
    """Parse supported query shapes without a general NLP system."""

    def parse(self, question: str) -> ParsedQuery:
        """Return a parsed query, or UNKNOWN when unsupported."""
        normalized = self._normalize_question(question)
        if not normalized:
            return ParsedQuery(Intent.UNKNOWN)
        for intent, pattern in QUERY_PATTERNS:
            match = pattern.match(normalized)
            if match is None:
                continue
            object_name = match.groupdict().get("object")
            return ParsedQuery(
                intent=intent,
                object_name=self.normalize_object(object_name) if object_name else None,
            )
        return ParsedQuery(Intent.UNKNOWN)

    @staticmethod
    def normalize_object(object_name: str) -> str:
        """Normalize detector category aliases."""
        normalized = " ".join(object_name.casefold().strip().split())
        return ALIASES.get(normalized, normalized)

    @staticmethod
    def _normalize_question(question: str) -> str:
        table = str.maketrans("", "", string.punctuation)
        return " ".join(question.casefold().translate(table).split())
