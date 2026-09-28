# World stage profile (before optimization)

Requested command: `python -m evaluation.perf --frames 2000 --video data/evaluation/vtest.avi`

The real clip contains 795 frames, so this command processes 795 (790 measured after warm-up), not 2000. Full stdout: world-before-clip.txt.

Additional explicitly labeled replay command: `python -m evaluation.perf --frames 2000 --video data/evaluation/vtest.avi --loop-video`

This processes 2000 real decoded frames (1995 measured), replaying at EOF while keeping all pipeline state. It does not represent 2000 unique source frames. Full stdout: world-before-replay.txt. Frames are streamed to avoid preloading large video buffers; decode remains outside the documented timing scope.

| Run | First 200 measured frames: world p50 ms | Last 200: world p50 ms | Median history entries first / last | Median active tracks first / last |
| --- | ---: | ---: | --- | --- |
| Original 795-frame clip | 11.5073 | 41.6493 | 629 / 2090 | 9 / 10 |
| Explicit 2000-frame replay | 11.5948 | 71.3321 | 629 / 3018.5 | 9 / 9 |

Cause: `WorldState.update` calls `deepcopy(self._registry.values())`, recursively reconstructing each active Track and every Detection in its entire history. `Tracker._update_matched_track` appends a Detection per match and does not bound that history. Snapshot construction therefore grows with cumulative observations, not just active track count. Belief application itself is a per-track loop.

Isolation evidence: `python -m evaluation.world_profile` (world-isolation-before.txt), explicitly synthetic and not detector/FPS evidence. With one track and unique immutable detections, p50 update time grows from 3.1331 ms at 200 history entries to 29.5920 ms at 2000. cProfile for one 2000-entry update records 314174 calls; recursive deepcopy occupies 0.136 of 0.137 seconds. These profiled times are separate from unprofiled medians.

Reported to the user before any world implementation edit. Proposed separate fix: detach mutable Track objects and full history lists, share frozen Detection values. Preserve all historical entries and snapshot isolation; do not silently truncate history. List copying remains O(history length), so the change will reduce rather than eliminate asymptotic growth. Tests establish the snapshot isolation contract before changing implementation.

Verification: 90 tests and 6 subtests pass (world-profile-pytest.txt); window/replay tests and full-history isolation tests included. No world behavior changes in this profiling commit.
