# Phase 3a-1: oracle decisions

User-authorized oracle corrections; no reasoning/planner behavior changes in step A.

| Case/change | Intended expectation | Source defining intent |
| --- | --- | --- |
| Reasoning cell phone_003 | `cell phone is near book.` | `reasoning/reasoning_engine.py:ReasoningEngine._collect_facts` applies `_display_name` to every nearby name; `_display_name` removes numeric instance suffixes. The existing subject in the same tuple is already `cell phone`, not `cell phone_003`. `NearbyRelationshipRule.infer` expresses that display-name relationship. |
| Reasoning keys_006 | `keys is near chair.` | Same display-name contract; existing subject is `keys`, not `keys_006`. No other conclusion in this tuple changed. |
| Planner remote_009 | `("Expand search area.",)` | `planning/planner_rules.py:ExpandSearchRule.applies` requires no useful evidence; `PlanningContext.has_useful_evidence` means location or nearby objects. `ExpandSearchRule.propose` defines the fallback action. The available pre-2b file at `7e4a0e1:evaluation/scenarios/planner_quality.py` is only a placeholder, so it cannot substantiate a remote_009 golden expectation; this correction is supported by the explicit rule contract and Phase 3a-1 A.2. |
| Delete unobserved_object_999 | Remove duplicate unknown-object case | Phase 3a-1 A.3: same no-evidence branch already covered by remote_009. |
| Delete empty-target golden case | Validate malformed goals in unit tests instead | Phase 3a-1 A.3 and B.6 explicitly separate invalid input validation from golden behavioral evaluation. |
| New cup_010 negative | Inspect (7, 8); forbid expansion | `FindObjectRule.applies/propose` uses a known location. `ExpandSearchRule.applies` is false when `has_useful_evidence` is true. |
| New bottle_011 negative | Inspect (9, 10); forbid `Search near *` | `SearchNearbyRule.applies` requires nonempty nearby objects; fixture has no relation or reasoning-derived neighbor. Forbidden entries use case-sensitive shell patterns so every nearby-search description is covered. |
| New bag_012 negative | Search near chair; forbid expansion | `SearchNearbyRule` consumes the NEAR relation, with name normalization in `_unique_display_names`. `has_useful_evidence` is true from nearby objects even without a known position; expansion must not apply. |
| New cart_011 reasoning negative | No conclusions, specifically no stationary conclusion | `StationaryObjectRule.applies` explicitly requires STATIC; this record is MOVING, with no movement event, neighbors, or disappearance evidence to trigger any other registered rule. All previous reasoning negatives retained. |

A planner case passes only when the complete ordered expected action tuple matches AND no actual action matches any forbidden pattern. These expectations were written from rule contracts and the user decision, not by copying observed outputs.

Step A verification: `python -m pytest -q`: 67 passed, 6 subtests passed. `python -m evaluation --markdown`: reasoning 9/9, planner 6/6. Full outputs: triage-oracles-pytest.txt and triage-oracles-evaluation.md.

Step B: `Goal.__post_init__` now rejects empty/whitespace-only targets with the existing `planning.exceptions.PlanningError`, as explicitly required by Phase 3a-1 B.6. Nonblank targets are preserved; planner rule behavior is unchanged. Unit tests cover empty, spaces, tabs/newlines, and preservation of a nonblank target. Verification: 71 passed, 6 subtests passed; reasoning 9/9 and planner 6/6. Full outputs: goal-pytest.txt and goal-evaluation.md.
