"""Measured benchmark for deterministic query-answering accuracy."""

from dataclasses import dataclass

from assistant import QueryEngine, QuerySource
from evaluation.benchmark import Benchmark
from evaluation.metrics import Score
from evaluation.scenarios.common import event, memory_with_records, record, timeline_with, track
from events import EventType
from memory import MemoryStatus


@dataclass(frozen=True)
class QueryCase:
    """One query and its expected observable answer properties."""

    intent: str
    question: str
    expected_source: QuerySource
    expected_text: str


def supported_cases() -> list[QueryCase]:
    """Return supported phrasings grouped by parser intent."""
    return [
        QueryCase("WHERE_IS", "where is the phone", QuerySource.CURRENT, "(10, 20)"),
        QueryCase("WHERE_IS", "where is the wallet", QuerySource.MEMORY, "(22, 33)"),
        QueryCase("WHERE_WAS", "where was the wallet", QuerySource.MEMORY, "(22, 33)"),
        QueryCase(
            "LAST_SEEN",
            "when was the wallet last seen",
            QuerySource.MEMORY,
            "07:43:10",
        ),
        QueryCase("VISIBILITY", "is the phone visible", QuerySource.CURRENT, "Yes."),
        QueryCase(
            "VISIBILITY",
            "is the wallet visible",
            QuerySource.MEMORY,
            "No.",
        ),
        QueryCase(
            "CURRENT_OBJECTS",
            "what objects do you see",
            QuerySource.CURRENT,
            "- cell phone",
        ),
        QueryCase(
            "RECENT_HISTORY",
            "what happened recently",
            QuerySource.TIMELINE,
            "Recently observed:",
        ),
        QueryCase(
            "RECENT_HISTORY",
            "what did you see earlier",
            QuerySource.TIMELINE,
            "Recently observed:",
        ),
        QueryCase(
            "UNKNOWN_OBJECT",
            "where is the remote",
            QuerySource.UNKNOWN,
            "reliable observation",
        ),
    ]


def paraphrase_cases() -> list[QueryCase]:
    """Return real-world paraphrases with expected answers."""
    return [
        *[
            QueryCase("PARAPHRASE_WHERE_PHONE", question, QuerySource.CURRENT, "(10, 20)")
            for question in [
                "where did I leave my phone",
                "can you locate my phone",
                "find my phone",
                "what is the phone location",
                "tell me where my phone is",
                "where is my phone",
                "where's the phone",
                "phone location please",
                "do you know where my phone is",
                "show me the phone",
            ]
        ],
        *[
            QueryCase("PARAPHRASE_WHERE_WALLET", question, QuerySource.MEMORY, "(22, 33)")
            for question in [
                "do you know where the wallet went",
                "where did the wallet go",
                "have you seen my wallet",
                "show me the wallet location",
                "where is my wallet",
                "where's the wallet",
                "where did I leave my wallet",
                "wallet location please",
                "find my wallet",
                "last wallet position",
            ]
        ],
        *[
            QueryCase("PARAPHRASE_VISIBLE_PHONE", question, QuerySource.CURRENT, "Yes.")
            for question in [
                "can you see the phone",
                "do you see my phone",
                "is the phone in frame",
                "is my phone visible",
                "phone visible?",
                "can the camera see my phone",
                "is the phone on camera",
                "do you currently see the phone",
                "is there a phone visible",
                "tell me if the phone is visible",
            ]
        ],
        *[
            QueryCase("PARAPHRASE_VISIBLE_WALLET", question, QuerySource.MEMORY, "No.")
            for question in [
                "is my wallet visible",
                "can you see the wallet",
                "do you see my wallet",
                "is the wallet in frame",
                "wallet visible?",
                "can the camera see my wallet",
                "is the wallet on camera",
                "do you currently see the wallet",
                "is there a wallet visible",
                "tell me if the wallet is visible",
            ]
        ],
        *[
            QueryCase("PARAPHRASE_LIST", question, QuerySource.CURRENT, "- cell phone")
            for question in [
                "what can you see right now",
                "list visible objects",
                "what is in view",
                "what is on camera",
                "anything visible",
                "show visible objects",
                "what objects are visible",
                "what are you seeing",
                "current objects please",
                "what does the camera see",
            ]
        ],
        *[
            QueryCase("PARAPHRASE_HISTORY", question, QuerySource.TIMELINE, "Recently observed:")
            for question in [
                "what happened before",
                "summarize recent observations",
                "what changed recently",
                "recent activity please",
                "what did the camera notice",
                "recent history",
                "what did you observe earlier",
                "anything happen recently",
                "show recent events",
                "what has been seen",
            ]
        ],
    ]


def evaluate(
    supported: list[QueryCase] | None = None,
    paraphrases: list[QueryCase] | None = None,
) -> Benchmark:
    """Run the real query engine against fixed current, memory, and timeline state."""
    engine = QueryEngine()
    current_tracks = [track("cell phone", track_id=1, center=(10, 20))]
    wallet_event = event(EventType.APPEARED, "wallet_002", 2, 0, (22, 33))
    bottle_event = event(EventType.APPEARED, "bottle_003", 3, 1, (44, 55))
    memory = memory_with_records([
        record(
            "wallet_002",
            2,
            MemoryStatus.LOST,
            position=(22, 33),
            events=[wallet_event],
        )
    ])
    timeline = timeline_with([wallet_event, bottle_event])
    supported_inputs = supported_cases() if supported is None else supported
    paraphrase_inputs = paraphrase_cases() if paraphrases is None else paraphrases

    supported_correct = _correct_count(
        engine,
        supported_inputs,
        current_tracks,
        memory,
        timeline,
    )
    paraphrase_correct = _correct_count(
        engine,
        paraphrase_inputs,
        current_tracks,
        memory,
        timeline,
    )
    intent_scores = _intent_scores(
        engine,
        supported_inputs,
        current_tracks,
        memory,
        timeline,
    )
    supported_total = len(supported_inputs)
    paraphrase_total = len(paraphrase_inputs)
    supported_score = Score(
        supported_correct / supported_total if supported_total else 0.0,
        supported_correct,
        supported_total,
        "supported questions",
    )
    paraphrase_score = Score(
        paraphrase_correct / paraphrase_total if paraphrase_total else 0.0,
        paraphrase_correct,
        paraphrase_total,
        "paraphrases",
    )
    return Benchmark(
        name="Query Accuracy",
        description=(
            "Real QueryEngine over fixed tracks, memory, and timeline; supported "
            "cases are grouped by intent and paraphrase coverage means expected "
            "source/text answered correctly."
        ),
        expected_result=(
            f"{supported_total} deduplicated supported questions and "
            f"{paraphrase_total} real-world paraphrases."
        ),
        actual_result=(
            f"supported={supported_correct}/{supported_total}; "
            f"paraphrase_coverage={paraphrase_correct}/{paraphrase_total}."
        ),
        score=supported_score,
        metrics=(*intent_scores, supported_score, paraphrase_score),
    )


def run() -> Benchmark:
    """Return the measured query accuracy benchmark."""
    return evaluate()


def _correct_count(
    engine: QueryEngine,
    cases: list[QueryCase],
    current_tracks: list[object],
    memory: object,
    timeline: object,
) -> int:
    return sum(
        1
        for case in cases
        if _is_correct(engine.answer(case.question, current_tracks, memory, timeline), case)
    )


def _intent_scores(
    engine: QueryEngine,
    cases: list[QueryCase],
    current_tracks: list[object],
    memory: object,
    timeline: object,
) -> tuple[Score, ...]:
    grouped: dict[str, list[QueryCase]] = {}
    for case in cases:
        grouped.setdefault(case.intent, []).append(case)
    scores: list[Score] = []
    for intent, intent_cases in sorted(grouped.items()):
        correct = _correct_count(engine, intent_cases, current_tracks, memory, timeline)
        total = len(intent_cases)
        scores.append(
            Score(
                correct / total if total else 0.0,
                correct,
                total,
                f"{intent} supported",
            )
        )
    return tuple(scores)


def _is_correct(response: object, case: QueryCase) -> bool:
    return (
        getattr(response, "source", None) is case.expected_source
        and case.expected_text in getattr(response, "answer", "")
    )
