"""Measured benchmark for deterministic planner quality."""

from dataclasses import dataclass
from fnmatch import fnmatchcase

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
    forbidden_actions: tuple[str, ...] = ()


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
            record(
                "keys_002", 2, MemoryStatus.LOST, position=(50, 60), events=[keys_event]
            ),
            record(
                "chair_003",
                3,
                MemoryStatus.STATIC,
                position=(55, 61),
                events=[chair_event],
            ),
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
            expected_actions=("Expand search area.",),
        ),
        # Independent negatives: explicit prohibitions also guard the oracle itself.
        PlannerCase(
            goal=_goal("cup_010"),
            planner=_planner(
                _knowledge(
                    [record("cup_010", 10, MemoryStatus.STATIC, position=(7, 8))], []
                )
            ),
            expected_actions=("Inspect last known location (7, 8).",),
            forbidden_actions=("Expand search area.",),
        ),
        PlannerCase(
            goal=_goal("bottle_011"),
            planner=_planner(
                _knowledge(
                    [record("bottle_011", 11, MemoryStatus.ACTIVE, position=(9, 10))],
                    [],
                )
            ),
            expected_actions=("Inspect last known location (9, 10).",),
            forbidden_actions=("Search near *",),
        ),
        PlannerCase(
            goal=_goal("bag_012"),
            planner=_planner(
                _knowledge(
                    [
                        record("bag_012", 12, MemoryStatus.LOST, position=None),
                        record("chair_013", 13, MemoryStatus.STATIC),
                    ],
                    [],
                    scene_with_near(12, 13, "bag_012", "chair_013"),
                )
            ),
            expected_actions=("Search near chair.",),
            forbidden_actions=("Expand search area.",),
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
        if actual == case.expected_actions and not any(
            fnmatchcase(action, forbidden)
            for action in actual
            for forbidden in case.forbidden_actions
        ):
            correct += 1
        else:
            mismatches.append(case.goal.target_object)
    total = len(measured_cases)
    return Benchmark(
        name="Planner Regression (golden cases)",
        description=(
            "Golden-output regression check for the real Planner over fixed "
            "knowledge/reasoning states; score is exact-match rate for ordered "
            "action descriptions AND absence of forbidden actions (shell-style patterns)."
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
