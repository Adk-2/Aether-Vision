"""Tests for deterministic, measured evaluation scenarios."""

from dataclasses import replace
from pathlib import Path
import sys
import unittest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from evaluation.evaluator import Evaluator
from evaluation.scenarios import (
    belief_stability,
    event_quality,
    identity_stability,
    planner_quality,
    query_accuracy,
    reasoning_accuracy,
)


class EvaluationScenarioTests(unittest.TestCase):
    def test_running_twice_gives_identical_markdown(self) -> None:
        first = Evaluator().run().to_markdown()
        second = Evaluator().run().to_markdown()

        self.assertEqual(first, second)

    def test_corrupting_identity_ground_truth_lowers_score(self) -> None:
        baseline = identity_stability.evaluate()
        corrupted = identity_stability.evaluate(
            frames=_wrong_multitrack_truth(identity_stability.noisy_multitrack_stream())
        )

        self.assertLess(corrupted.score.value, baseline.score.value)

    def test_corrupting_belief_ground_truth_lowers_score(self) -> None:
        baseline = belief_stability.evaluate()
        corrupted = belief_stability.evaluate(
            frames=_wrong_multitrack_truth(belief_stability.noisy_multitrack_stream())
        )

        self.assertLess(corrupted.score.value, baseline.score.value)

    def test_corrupting_event_ground_truth_lowers_score(self) -> None:
        baseline = event_quality.evaluate()
        corrupted = event_quality.evaluate(
            [
                replace(frame, expected_events=())
                for frame in event_quality.scripted_frames()
            ]
        )

        self.assertLess(corrupted.score.value, baseline.score.value)

    def test_corrupting_reasoning_golden_output_lowers_score(self) -> None:
        baseline = reasoning_accuracy.evaluate()
        cases = reasoning_accuracy.cases()
        cases[0] = replace(cases[0], expected_conclusions=("wrong",))
        corrupted = reasoning_accuracy.evaluate(cases)

        self.assertLess(corrupted.score.value, baseline.score.value)

    def test_corrupting_planner_golden_output_lowers_score(self) -> None:
        baseline = planner_quality.evaluate()
        cases = planner_quality.cases()
        cases[0] = replace(cases[0], expected_actions=("wrong",))
        corrupted = planner_quality.evaluate(cases)

        self.assertLess(corrupted.score.value, baseline.score.value)

    def test_corrupting_query_expected_answer_lowers_score(self) -> None:
        baseline = query_accuracy.evaluate()
        cases = query_accuracy.supported_cases()
        cases[0] = replace(cases[0], expected_text="wrong")
        corrupted = query_accuracy.evaluate(supported=cases)

        self.assertLess(corrupted.score.value, baseline.score.value)

    def test_empty_input_lists_are_respected(self) -> None:
        # Phase 2c item 13 explicitly replaces the old empty-input 0% contract.
        for call in [
            lambda: identity_stability.evaluate(frames=[], adaptation_frames=[]),
            lambda: belief_stability.evaluate(frames=[], adaptation_frames=[]),
            lambda: event_quality.evaluate([]),
            lambda: reasoning_accuracy.evaluate([]),
            lambda: planner_quality.evaluate([]),
            lambda: query_accuracy.evaluate(supported=[], paraphrases=[]),
        ]:
            with self.subTest(call=call), self.assertRaises(ValueError):
                call()


def _wrong_multitrack_truth(frames: list[object]) -> list[object]:
    corrupted = []
    for frame in frames:
        observations = tuple(
            replace(observation, expected_label="wrong")
            for observation in frame.observations
        )
        corrupted.append(replace(frame, observations=observations))
    return corrupted


if __name__ == "__main__":
    unittest.main()
