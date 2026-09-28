# Belief startup gate

Reuse `belief_policy.MIN_CONSECUTIVE_OBSERVATIONS` (10) for initial publication. Pending state counts consecutive matching resolved identity labels per track, clears on absence/label change, and is not exposed by update/get/all or persisted. Published switching policy is unchanged. `replace_all` clears pending candidates. The evaluator treats an absent belief as not correct; it does not remove unpublished frames from accuracy denominators.

| 20-seed metric | Before | After |
| --- | --- | --- |
| Identity steady-state mean/min/max | 100% / 100% / 100% | 100% / 100% / 100% |
| Identity cold-start mean/min/max frames | 1.325 / 1 / 4 | 1.325 / 1 / 4 |
| Belief steady-state mean/min/max | 99.5667% / 97.3333% / 100% | 100% / 100% / 100% |
| Belief pooled steady-state correct | 8961/9000 | 9000/9000 |
| Belief cold-start mean/min/max frames | 5.45 / 1 / 28 | 10.375 / 10 / 13 |
| Identity / belief adaptation frames | 31 / 43 | 31 / 43 |
| Largest burst neither flips, tested L=1..20 | 20 | 20 |

Tradeoff: average time to the first correct published belief INCREASES, while the worst observed startup decreases from 28 to 13 and steady-state errors disappear on these synthetic seeds. This is not a claim of uniformly faster startup. A wrong identity stable for 10 frames can still publish a wrong belief; the gate does not establish ground truth.

Evidence: before.md (post-triage baseline), belief-evaluation.md (full after output), belief-pytest.txt (85 tests and 6 subtests pass). Integration tests exercise memory, knowledge location/state/belief queries, reasoning, planning, world/event flow, and pipeline belief application across all unpublished frames and first publication. No downstream consumer behavior needed changing. Existing pruning tests now explicitly establish a belief for 10 observations before exercising pruning, avoiding a vacuous test.
