# Phase 4 step 2: real-video evaluator

Command:

```text
python -m evaluation.real_video_eval --video PATH --labels PATH
```

The evaluator loads, validates, and SHA-256 hashes `labels.json` before detector construction or inference. The labeling helper now writes `annotation_status: "unlabeled"`; the evaluator refuses to run until the human changes it to `"complete"` after labeling. This is an explicit guard against viewing output before ground truth is fixed.

The measured chain is:

```text
VisionDetector.detect
→ DetectionAdapter.convert
→ ConfidenceFilter.filter
→ Tracker.update
→ DetectionStabilizer.stabilize
→ IdentityResolver.update
→ BeliefEngine.update
→ apply beliefs + WorldState.update
→ EventEngine.generate_events
→ EventFilter.filter_events
```

No tracker, identity, belief, event, or detector implementation was modified.

Measurement definitions:

- Detection matching is greedy, one-to-one nearest-center association, identical in ordering principle to `tracking.association.AssociationEngine`. Its default tolerance reuses `DEFAULT_DISTANCE_THRESHOLD = 50.0` pixels; it is printed in the report and can be overridden with `--center-tolerance`.
- Classes use the existing query class normalizer, so hand label `phone` compares to detector label `cell phone`.
- A spatially matched detection with the wrong class contributes one false positive and one false negative. Unmatched detections and labels contribute false positives and false negatives respectively.
- Identity accuracy is evaluated on ground-truth objects spatially matched to currently observed tracks. A missing identity is incorrect. It is not silently omitted.
- The last matched track ID is retained per hand-written physical-object tag. A later different track ID for that tag is reported as an ID switch, including across an occlusion gap.
- Each labeled frame closes the event interval after the previous labeled frame through the current one. This permits sparse frame extraction without discarding intermediate predicted transitions.
- Filtered `STARTED_MOVING` and `STOPPED_MOVING` are compared to the hand-label vocabulary as `moved` and `stopped`. `appeared` and `disappeared` retain their names. `none` adds no positive ground-truth event and therefore exposes any predicted transition as a false positive.
- Predicted events are associated to physical tags through current or previously established track/tag matches. Events from an unmapped track remain concrete false positives under `track:<id>`.
- Timing discards the first five frames only from latency/FPS samples; all decoded frames still run through the pipeline and all labeled frames are scored. Decoding is outside the timed chain.
- Output contains per-clip and pooled detection/event precision and recall with raw TP/FP/FN, identity correct/total, ID-switch counts, FPS, detector-excluded FPS, and p50/p95 for every stage. The report ranks up to ten concrete failures by severity, then clip/frame.

Verified cases include perfect end-to-end scoring, an ID switch `track 0 -> 1`, exact missed-event reporting, a wrong detection class, a sparse six-frame event interval, one-to-one matching, invalid/incomplete labels, and digest capture.

Raw verification output:

```text
2 files left unchanged
All checks passed!
.................................................................. [ 62%]
........................................                                 [100%]
106 passed, 6 subtests passed in 7.81s
```

No self-recorded clip or completed hand labels existed at this step, so this evidence contains no claimed real-video metric.
