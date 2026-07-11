"""Reusable metric primitives for Project Aether evaluation."""

from dataclasses import dataclass


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

    def __post_init__(self) -> None:
        """Keep scores bounded to the normalized 0..1 range."""
        if not 0.0 <= self.value <= 1.0:
            raise ValueError("Score must be between 0.0 and 1.0")

    @property
    def percentage(self) -> float:
        """Return this score as a percentage."""
        return self.value * 100.0
