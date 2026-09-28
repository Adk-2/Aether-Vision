from dataclasses import replace
from evaluation.scenarios import planner_quality as p, reasoning_accuracy as r
from reasoning import ReasoningEngine


def test_golden_cases_and_real_negatives():
    assert r.run().score.raw_counts == "9/9 cases"
    assert p.run().score.raw_counts == "6/6 cases"
    negatives = [c for c in p.cases() if c.forbidden_actions]
    assert len(negatives) >= 3
    assert all(c.goal.target_object.strip() for c in p.cases())


def test_forbidden_actions_override_even_matching_expected_tuple():
    case = p.cases()[0]
    assert p.evaluate([case]).score.value == 1
    assert (
        p.evaluate([replace(case, forbidden_actions=case.expected_actions)]).score.value
        == 0
    )
    nearby = p.cases()[1]
    assert (
        p.evaluate([replace(nearby, forbidden_actions=("Search near *",))]).score.value
        == 0
    )


def test_moving_negative_rejects_stationary_rule():
    case = next(c for c in r.cases() if c.object_name == "cart_011")
    results = ReasoningEngine(case.knowledge, r._rules()).infer(case.object_name)
    assert not any(
        "StationaryObjectRule" in result.triggered_rules for result in results
    )
    corrupted = replace(
        case,
        expected_conclusions=("cart is probably still where it was last observed.",),
    )
    assert r.evaluate([corrupted]).score.value == 0
