"""Reusable metric primitives for Project Aether evaluation."""

from dataclasses import dataclass
from math import isclose


@dataclass(frozen=True)
class Percentage:
    """Represent a percentage metric."""

    numerator: float
    denominator: float

    @property
    def value(self) -> float:
        """Return the percentage value in the range 0..100."""
        if self.denominator == 0:
            return 0.0
        return (self.numerator / self.denominator) * 100.0


@dataclass(frozen=True)
class Counter:
    """Represent a count metric."""

    value: int = 0

    def increment(self, amount: int = 1) -> "Counter":
        """Return a new counter with the supplied amount added."""
        return Counter(self.value + amount)


@dataclass(frozen=True)
class Average:
    """Represent an average metric."""

    total: float
    count: int

    @property
    def value(self) -> float:
        """Return the average value."""
        if self.count == 0:
            return 0.0
        return self.total / self.count


@dataclass(frozen=True)
class Score:
    """Represent a normalized evaluation score."""

    value: float
    numerator: float | None = None
    denominator: float | None = None
    label: str = "correct"
    raw_counts_text: str | None = None

    def __post_init__(self) -> None:
        """Keep scores bounded to the normalized 0..1 range."""
        if not 0.0 <= self.value <= 1.0:
            raise ValueError("Score must be between 0.0 and 1.0")
        if self.numerator is None or self.denominator is None:
            return
        expected = 0.0 if self.denominator == 0 else self.numerator / self.denominator
        if not isclose(self.value, expected, rel_tol=1e-9, abs_tol=1e-9):
            raise ValueError("Score value must match numerator and denominator")

    @property
    def percentage(self) -> float:
        """Return this score as a percentage."""
        return self.value * 100.0

    @property
    def raw_counts(self) -> str:
        """Return the score's raw counts when available."""
        if self.raw_counts_text is not None:
            return self.raw_counts_text
        if self.numerator is None or self.denominator is None:
            return "n/a"
        return f"{self._format(self.numerator)}/{self._format(self.denominator)} {self.label}"

    @property
    def display(self) -> str:
        """Return a percentage and matching raw-count description."""
        return f"{self.percentage:.2f}% ({self.raw_counts})"

    @staticmethod
    def _format(value: float) -> str:
        return str(int(value)) if float(value).is_integer() else f"{value:.4f}"
