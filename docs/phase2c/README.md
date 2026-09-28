# Phase 2c evaluation evidence

Only evaluation, evaluation tests, evidence, and the downloaded-clip ignore rule change. Algorithm/policy implementations are untouched.

## Oracle sources and measurement definitions

- The sole modification to an existing event expectation is `(8, 1, STOPPED)`. `events/event_engine.py:EventEngine._movement_events` resets the counter on every center change and emits STOPPED exactly at the configured threshold (2 in the raw fixture). All eight 1-pixel MOVED expectations remain absent.
- New filtered fixture is hand-authored in `evaluation/scenarios/event_quality.py:pipeline_frames`, never generated from predictions. Intended jitter rejection comes from Phase 2c A.1–3. `events/event_policy.py:DEFAULT_STOPPED_FRAME_THRESHOLD` sets the pipeline threshold to 3. `EventFilter._filter_event`, `_started_moving`, and `_stopped_moving` define appearance/disappearance reset and movement transitions, including suppression of redundant stops. `PerceptionPipeline.process_next_frame` establishes engine-then-filter order. Jitter membership is an independent fixture annotation; its rate counts frames emitting any raw/semantic movement or stop event, not events or tracks.
- Phase 2c B.5–7 defines the new 20 seeds, 15-observation exclusion per track, 30+100 relabel stream, and L=1..20 wrong-label bursts. Cold start counts the first observation as frame 1 and aggregates track/seed samples; steady-state mean/min/max aggregates seed accuracies. Censored cold starts show n/a with their observed bounds. Burst trials independently establish a track for 30 frames, then inspect both components throughout the burst and 30 recovery frames; 20 is the tested upper bound, not an unlimited guarantee.
- Existing query source/text expectations and paraphrases are retained. The old UNKNOWN_OBJECT grouping is correctly classified as WHERE_IS per `assistant/query.py:QUERY_PATTERNS`; its UNKNOWN response oracle is unchanged. New question/state fixtures follow `assistant/query_engine.py` contracts: `_answer_where_is` prefers visible locations and enumerates multiple instances; `_answer_where_was` reads latest memory; `_answer_last_seen` uses the latest observation; `_answer_visibility` separates visible, known-lost, and never-seen; `_answer_current_objects` lists unique visible classes; `_answer_recent_history` reads timeline or abstains. New moved fixture records the new position/time and STARTED_MOVING history. These fixtures do not derive truth by calling QueryEngine.
- Phase 2c E.13 replaces the former test expectation that empty inputs score 0% with ValueError. No reasoning/planner golden expectations changed.
- Confidently wrong means any non-UNKNOWN response failing the source/text oracle, regardless of numerical confidence. Both sets report count/total. The stock paraphrases all abstain; a separate test supplies a supported phrasing to verify wrong-answer sensitivity in the paraphrase metric.

## Performance scope and reproducibility

Video: OpenCV sample `vtest.avi`, downloaded from https://raw.githubusercontent.com/opencv/opencv/4.x/samples/data/vtest.avi

SHA256: `45cddc9490be69345cbdab64ca583be65987e864ca408038e648db99e10516cf`

Local path: `data/evaluation/vtest.avi` (downloaded binary excluded from Git). Model: repository `yolov8n.pt`. The real path calls detector, adapter, confidence filter, tracker, stabilizer, identity, belief, belief application/world snapshot, event engine/filter, memory/timeline, and query. Five frames execute but contribute no timing samples. FPS covers detect through query, including orchestration, but excludes video decoding, renderer, persistence, and scene/reasoning/planner work. Detector-excluded FPS subtracts measured detector time from that same elapsed interval. Latency percentiles use linear interpolation. Timing is machine/load-dependent.

## Observed weaknesses (left unfixed)

- Raw engine emits MOVED for all eight annotated jitter frames.
- Filtered fixture emits an early STARTED_MOVING on jitter and misses the intended later start.
- Belief can retain a wrong initial label into steady state; cold starts and accuracy vary with seed.
- Sustained relabel adaptation takes multiple frames in both components.
- All existing paraphrases abstain rather than return their intended answers.
- Existing reasoning golden cases remain 6/8 and planner golden cases remain 2/5; their mismatches are printed and their oracles are unchanged.

Raw command output is saved verbatim in `pytest.txt`, `evaluation-markdown.txt`, and `perf-video.txt`. Tests cover metric sensitivity to corrupted oracles, deterministic seeds/output, score count consistency, empty inputs, video errors, stage order, and warm-up exclusion. Jitter sensitivity corrupts jitter membership, because changing unrelated expected event tuples must not change that rate.

Final checks: 64 tests and 6 subtests passed; Ruff passed for evaluation and the new tests; `git diff --check` passed. A direct comparison against the pre-change Git fixtures verified the sole raw-event oracle change and preservation of every existing query source/text oracle.
