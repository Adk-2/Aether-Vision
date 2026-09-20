"""Measured benchmark for deterministic planner quality."""

from dataclasses import dataclass

from evaluation.benchmark import Benchmark
from evaluation.metrics import Score
from evaluation.scenarios.common import BASE_TIME, event, record, scene_with_near
from evaluation.scenarios.reasoning_accuracy import _knowledge, _rules
from events import EventType
from memory import MemoryStatus
from planning import Goal, Planner, PlannerRules
from reasoning import ReasoningEngine


@dataclass(frozen=True)
class PlannerCase:
    """One deterministic planner input and expected action descriptions."""

    goal: Goal
    planner: Planner
    expected_actions: tuple[str, ...]


def cases() -> list[PlannerCase]:
    """Return fixed planner cases with known exact action descriptions."""
    phone_event = event(EventType.APPEARED, "cell phone_001", 1, 0, (12, 34))
    keys_event = event(EventType.APPEARED, "keys_002", 2, 0, (50, 60))
    chair_event = event(EventType.APPEARED, "chair_003", 3, 0, (55, 61))
    phone_knowledge = _knowledge(
        [
            record(
                "cell phone_001",
                1,
                MemoryStatus.STATIC,
                position=(12, 34),
                events=[phone_event],
            )
        ],
        [phone_event],
    )
    nearby_knowledge = _knowledge(
        [
            record("keys_002", 2, MemoryStatus.LOST, position=(50, 60), events=[keys_event]),
            record("chair_003", 3, MemoryStatus.STATIC, position=(55, 61), events=[chair_event]),
        ],
        [keys_event, chair_event],
        scene_with_near(2, 3, "keys_002", "chair_003"),
    )
    unknown_knowledge = _knowledge([], [])
    return [
        PlannerCase(
            goal=_goal("cell phone_001"),
            planner=_planner(phone_knowledge),
            expected_actions=("Inspect last known location (12, 34).",),
        ),
        PlannerCase(
            goal=_goal("keys_002"),
            planner=_planner(nearby_knowledge),
            expected_actions=(
                "Inspect last known location (50, 60).",
                "Search near chair.",
            ),
        ),
        PlannerCase(
            goal=_goal("remote_009"),
            planner=_planner(unknown_knowledge),
            expected_actions=(),
        ),
        PlannerCase(
            goal=_goal(""),
            planner=_planner(unknown_knowledge),
            expected_actions=(),
        ),
        PlannerCase(
            goal=_goal("unobserved_object_999"),
            planner=_planner(unknown_knowledge),
            expected_actions=(),
        ),
    ]


def evaluate(input_cases: list[PlannerCase] | None = None) -> Benchmark:
    """Run the real planner and score exact action-list matches."""
    measured_cases = cases() if input_cases is None else input_cases
    correct = 0
    mismatches: list[str] = []
    for case in measured_cases:
        plan = case.planner.create_plan(case.goal)
        actual = tuple(action.description for action in plan.actions)
        if actual == case.expected_actions:
            correct += 1
        else:
            mismatches.append(case.goal.target_object)
    total = len(measured_cases)
    return Benchmark(
        name="Planner Regression (golden cases)",
        description=(
            "Golden-output regression check for the real Planner over fixed "
            "knowledge/reasoning states; score is exact-match rate for ordered "
            "action descriptions, including negative cases where no action is "
            "expected."
        ),
        expected_result=f"{total} exact ordered action lists.",
        actual_result=(
            f"correct={correct}/{total}; mismatches={mismatches or 'none'}."
        ),
        score=Score(correct / total if total else 0.0, correct, total, "cases"),
    )


def run() -> Benchmark:
    """Return the measured planner quality benchmark."""
    return evaluate()


def _planner(knowledge: object) -> Planner:
    return Planner(
        knowledge,
        ReasoningEngine(knowledge, _rules()),
        PlannerRules(),
    )


def _goal(target_object: str) -> Goal:
    return Goal(
        goal_type="find",
        target_object=target_object,
        priority=1,
        timestamp=BASE_TIME,
    )
