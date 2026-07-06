"""Exceptions raised by the knowledge layer."""


class KnowledgeError(Exception):
    """Base error raised by knowledge orchestration."""


class KnowledgeQueryError(KnowledgeError):
    """Raised when a structured knowledge query is invalid."""
