"""Human-readable console reports for evaluation runs."""

from dataclasses import dataclass, field

from .benchmark import Benchmark


@dataclass(frozen=True)
class EvaluationReport:
    """Represent the result of a complete benchmark run."""

    benchmarks: list[Benchmark] = field(default_factory=list)

    @property
    def overall_score(self) -> float:
        """Return the mean normalized score across all benchmarks."""
        if not self.benchmarks:
            return 0.0
        return sum(benchmark.score.value for benchmark in self.benchmarks) / len(
            self.benchmarks
        )

    def to_console_text(self) -> str:
        """Return a human-readable benchmark report."""
        lines = [
            "========== Project Aether Evaluation ==========",
            "",
            f"Benchmarks: {len(self.benchmarks)}",
            f"Overall Score: {self.overall_score:.2f}",
        ]
        for index, benchmark in enumerate(self.benchmarks, start=1):
            lines.extend(
                [
                    "",
                    f"{index}. {benchmark.name}",
                    f"Description: {benchmark.description}",
                    f"Expected: {benchmark.expected_result}",
                    f"Actual: {benchmark.actual_result}",
                    f"Score: {benchmark.score.value:.2f}",
                ]
            )
        lines.extend(["", "=============================================="])
        return "\n".join(lines)

    def print_console(self) -> None:
        """Print the benchmark report to stdout."""
        print(self.to_console_text())
