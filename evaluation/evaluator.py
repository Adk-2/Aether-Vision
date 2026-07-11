"""Evaluation runner for Project Aether benchmarks."""

from collections.abc import Callable

from .benchmark import Benchmark
from .report import EvaluationReport
from .scenarios import (
    belief_stability,
    event_quality,
    identity_stability,
    planner_quality,
    reasoning_accuracy,
)

Scenario = Callable[[], Benchmark]


class Evaluator:
    """Run benchmark scenarios and produce an evaluation report."""

    def __init__(self, scenarios: list[Scenario] | None = None) -> None:
        self._scenarios = scenarios or [
            identity_stability.run,
            belief_stability.run,
            event_quality.run,
            reasoning_accuracy.run,
            planner_quality.run,
        ]

    def run(self) -> EvaluationReport:
        """Run every configured benchmark scenario."""
        return EvaluationReport([scenario() for scenario in self._scenarios])


def main() -> None:
    """Run evaluation benchmarks and print a console report."""
    Evaluator().run().print_console()


if __name__ == "__main__":
    main()
