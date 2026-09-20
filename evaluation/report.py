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
        ]
        for index, benchmark in enumerate(self.benchmarks, start=1):
            metric_text = "; ".join(
                f"{score.label}: {score.display}"
                for score in benchmark.reported_metrics
            )
            lines.extend(
                [
                    "",
                    f"{index}. {benchmark.name}",
                    f"Description: {benchmark.description}",
                    f"Expected: {benchmark.expected_result}",
                    f"Actual: {benchmark.actual_result}",
                    f"Metrics: {metric_text}",
                ]
            )
        lines.extend(
            [
                "",
                "Note: scenarios are synthetic/scripted and are not measured on real video.",
                "==============================================",
            ]
        )
        return "\n".join(lines)

    def to_markdown(self) -> str:
        """Return a Markdown table for benchmark results."""
        lines = [
            "| Scenario | Computation | Metrics |",
            "| --- | --- | --- |",
        ]
        for benchmark in self.benchmarks:
            metrics = "<br>".join(
                f"{score.label}: {score.display}"
                for score in benchmark.reported_metrics
            )
            lines.append(
                "| "
                f"{benchmark.name} | "
                f"{self._cell(benchmark.description)} | "
                f"{metrics} |"
            )
        lines.append(
            "| Note | Scenarios are synthetic/scripted and are not measured on real video. | |"
        )
        return "\n".join(lines)

    def print_console(self) -> None:
        """Print the benchmark report to stdout."""
        print(self.to_console_text())

    @staticmethod
    def _cell(value: str) -> str:
        return value.replace("|", "\\|").replace("\n", " ")
