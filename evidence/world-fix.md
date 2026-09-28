# Separate world-copy optimization

Applied only after reporting and committing the growth diagnosis (f7cc696). `WorldState.update` now uses dataclass replacement for each Track and a detached copy of the complete history list. It shares frozen Detection values, whose fields are immutable. Snapshot fields, full history, active filtering, timestamps, and previous/current snapshot isolation are preserved. No tracking history truncation or policy change.

| Measured window | Before world p50 ms | After world p50 ms |
| --- | ---: | ---: |
| Original clip: first 200 (6-205) | 11.5073 | 0.0626 |
| Original clip: last 200 (596-795) | 41.6493 | 0.0959 |
| Explicit replay: first 200 (6-205) | 11.5948 | 0.0670 |
| Explicit replay: last 200 (1801-2000) | 71.3321 | 0.1272 |
| Synthetic isolation: 200 history entries | 3.1331 | 0.0041 |
| Synthetic isolation: 2000 history entries | 29.5920 | 0.0086 |

After-run track/history window counts exactly match before-run counts. Real replay world p50/p95 overall: 42.9737/83.5749 ms before, 0.0994/0.1984 ms after. Measured replay mean FPS: 11.2749 before, 30.0552 after; excluding detector: 20.6791 before, 274.9140 after. Detector timing also varied (p50 39.7635 vs 27.4550 ms), so do not attribute the entire end-to-end FPS difference solely to this edit. Use isolated world medians and stage timings for the specific improvement.

Residual limitation: complete history lists still grow and copying references is still O(total history entries). The optimization removes recursive object reconstruction; it does not make history bounded or prove constant-time snapshots. The replay contains repeated footage with continuous pipeline state, not 2000 unique source frames.

Raw outputs: world-after-clip.txt, world-after-replay.txt, world-isolation-after.txt. Verification: 90 tests and 6 subtests pass (world-fix-pytest.txt); full-history mutation/isolation regression tests pass. The user's pre-existing data/aether_memory.json change is excluded.
