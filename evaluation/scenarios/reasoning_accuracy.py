"""Measured benchmark for deterministic reasoning accuracy."""

from dataclasses import dataclass

from belief import BeliefEngine
from evaluation.benchmark import Benchmark
from evaluation.metrics import Score
from evaluation.scenarios.common import (
    event,
    memory_with_records,
    record,
    scene_with_near,
    timeline_with,
)
from events import EventType
from knowledge import KnowledgeEngine
from memory import MemoryStatus
from reasoning import (
    CarryAwayRule,
    NearbyRelationshipRule,
    ObjectPermanenceRule,
    OcclusionRule,
    ReasoningEngine,
    RecentlyMovedRule,
    RuleRegistry,
    StationaryObjectRule,
)
from scene import SceneGraph


@dataclass(frozen=True)
class ReasoningCase:
    """One deterministic reasoning input and expected conclusions."""

    object_name: str
    knowledge: KnowledgeEngine
    expected_conclusions: tuple[str, ...]


def cases() -> list[ReasoningCase]:
    """Return fixed reasoning cases with known exact conclusions."""
    cup_event = event(EventType.APPEARED, "cup_001", 1, 0)
    bag_events = [
        event(EventType.APPEARED, "bag_002", 2, 0),
        event(EventType.MOVED, "bag_002", 2, 1),
    ]
    phone_event = event(EventType.APPEARED, "cell phone_003", 3, 0)
    book_event = event(EventType.APPEARED, "book_004", 4, 0)
    wallet_events = [
        event(EventType.APPEARED, "wallet_005", 5, 0),
        event(EventType.DISAPPEARED, "wallet_005", 5, 1),
    ]
    keys_events = [
        event(EventType.APPEARED, "keys_006", 6, 0),
        event(EventType.DISAPPEARED, "keys_006", 6, 1),
    ]
    chair_event = event(EventType.APPEARED, "chair_007", 7, 0)
    lamp_event = event(EventType.APPEARED, "lamp_008", 8, 0)
    box_events = [
        event(EventType.APPEARED, "box_009", 9, 0),
        event(EventType.STOPPED, "box_009", 9, 1),
    ]
    return [
        ReasoningCase(
            object_name="cup_001",
            knowledge=_knowledge(
                [record("cup_001", 1, MemoryStatus.STATIC, events=[cup_event])],
                [cup_event],
            ),
            expected_conclusions=(
                "cup is probably still where it was last observed.",
            ),
        ),
        ReasoningCase(
            object_name="bag_002",
            knowledge=_knowledge(
                [record("bag_002", 2, MemoryStatus.MOVING, seconds=1, events=bag_events)],
                bag_events,
            ),
            expected_conclusions=("bag was recently moved.",),
        ),
        ReasoningCase(
            object_name="cell phone_003",
            knowledge=_knowledge(
                [
                    record("cell phone_003", 3, MemoryStatus.STATIC, events=[phone_event]),
                    record("book_004", 4, MemoryStatus.STATIC, events=[book_event]),
                ],
                [phone_event, book_event],
                scene_with_near(3, 4, "cell phone_003", "book_004"),
            ),
            expected_conclusions=(
                "cell phone is probably still where it was last observed.",
                "cell phone is near book_004.",
            ),
        ),
        ReasoningCase(
            object_name="wallet_005",
            knowledge=_knowledge(
                [
                    record(
                        "wallet_005",
                        5,
                        MemoryStatus.LOST,
                        seconds=1,
                        events=wallet_events,
                    )
                ],
                wallet_events,
            ),
            expected_conclusions=(
                "wallet probably still exists outside the current camera view.",
            ),
        ),
        ReasoningCase(
            object_name="keys_006",
            knowledge=_knowledge(
                [
                    record("keys_006", 6, MemoryStatus.LOST, seconds=1, events=keys_events),
                    record("chair_007", 7, MemoryStatus.STATIC, events=[chair_event]),
                ],
                [*keys_events, chair_event],
                scene_with_near(6, 7, "keys_006", "chair_007"),
            ),
            expected_conclusions=(
                "keys is near chair_007.",
                "keys is probably occluded.",
                "keys probably still exists outside the current camera view.",
            ),
        ),
        ReasoningCase(
            object_name="lamp_008",
            knowledge=_knowledge(
                [record("lamp_008", 8, MemoryStatus.ACTIVE, events=[lamp_event])],
                [lamp_event],
            ),
            expected_conclusions=(),
        ),
        ReasoningCase(
            object_name="box_009",
            knowledge=_knowledge(
                [
                    record(
                        "box_009",
                        9,
                        MemoryStatus.MOVING,
                        seconds=1,
                        events=box_events,
                    )
                ],
                box_events,
            ),
            expected_conclusions=(),
        ),
        ReasoningCase(
            object_name="remote_010",
            knowledge=_knowledge([], []),
            expected_conclusions=(),
        ),
    ]


def evaluate(input_cases: list[ReasoningCase] | None = None) -> Benchmark:
    """Run real reasoning rules and score exact conclusion-set matches."""
    measured_cases = cases() if input_cases is None else input_cases
    correct = 0
    mismatches: list[str] = []
    for case in measured_cases:
        engine = ReasoningEngine(case.knowledge, _rules())
        actual = tuple(result.conclusion for result in engine.infer(case.object_name))
        if actual == case.expected_conclusions:
            correct += 1
        else:
            mismatches.append(case.object_name)
    total = len(measured_cases)
    return Benchmark(
        name="Reasoning Regression (golden cases)",
        description=(
            "Golden-output regression check for real ReasoningEngine rules over "
            "fixed memory/timeline/scene states; score is exact-match rate for "
            "conclusion tuples."
        ),
        expected_result=f"{total} exact conclusion tuples.",
        actual_result=(
            f"correct={correct}/{total}; mismatches={mismatches or 'none'}."
        ),
        score=Score(correct / total if total else 0.0, correct, total, "cases"),
    )


def run() -> Benchmark:
    """Return the measured reasoning accuracy benchmark."""
    return evaluate()


def _knowledge(
    records: list[object],
    events: list[object],
    scene: SceneGraph | None = None,
) -> KnowledgeEngine:
    return KnowledgeEngine(
        memory_with_records(records),
        timeline_with(events),
        scene if scene is not None else SceneGraph(),
        BeliefEngine(),
    )


def _rules() -> RuleRegistry:
    registry = RuleRegistry()
    registry.register(StationaryObjectRule())
    registry.register(NearbyRelationshipRule())
    registry.register(RecentlyMovedRule())
    registry.register(OcclusionRule())
    registry.register(CarryAwayRule())
    registry.register(ObjectPermanenceRule())
    return registry
