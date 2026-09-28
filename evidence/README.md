# Phase 3a evidence index

All steps completed with separate commits. Raw command outputs are preserved as captured.

| Step | Commit | Evidence |
| --- | --- | --- |
| Oracle corrections and real negatives | 283e753 | triage.md, triage-oracles-evaluation.md, triage-oracles-pytest.txt |
| Reject blank goals | 28460be | goal-evaluation.md, goal-pytest.txt |
| Post-triage baseline | fd24647 | before.md, before-metrics.json, baseline.md |
| Event jitter sweep and fix | 6899777 | event-sweep.md, event-threshold.md, event-evaluation.md, event-pytest.txt |
| Belief publication gate | 24e0331 | belief-startup.md, belief-evaluation.md, belief-pytest.txt |
| World growth diagnosis (before fix) | f7cc696 | world-profile.md, world-before-clip.txt, world-before-replay.txt, world-isolation-before.txt, world-profile-pytest.txt |
| Separate world-copy fix | 67ca05a | world-fix.md, world-after-clip.txt, world-after-replay.txt, world-isolation-after.txt, world-fix-pytest.txt |
| Final verification and full comparison | This commit | after.md, after-metrics.json, comparison.md, pytest.txt |

The baseline was saved only after both triage commits. comparison.md covers every evaluation metric and all recorded stage p50/p95, FPS, and first/last-window measurements. The final raw pytest output is 90 passed, 6 subtests passed in 16.25s. No implementation changed after that run.

Caveats: the 1-pixel event threshold is tuned on synthetic data; belief average cold-start latency increases while worst observed startup and steady-state accuracy improve; paraphrases still abstain. The original real clip is 795 frames; the separately labeled 2000-frame replay is repeated footage with continuous state. World history remains complete and unbounded, so copying its list is still linear.

The pre-existing user modification to data/aether_memory.json was neither staged nor edited: SHA256 remained 3a70b279fb04b2e8e5391ac759510a18630c136b110d8d0456eb0e3b387dd5e8 throughout the task. Reasoning/planner rules were not changed; Goal validation is the explicitly authorized input fix.
