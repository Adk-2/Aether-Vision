# Phase 4 step 3: measurement-only scope audit

Compared Phase 4 commits against their starting commit `a6e781e`.

```text
.gitignore
evaluation/label_video.py
evaluation/real_video_eval.py
evidence/phase4_labeling.md
evidence/phase4_real_eval.md
tests/test_label_video.py
tests/test_real_video_eval.py
ALGORITHM_AUDIT=unchanged
```

The audit command specifically checked these paths and found no differences:

```text
tracking/
identity/
belief/
events/
vision/
pipeline/perception_pipeline.py
```

Focused verification of the real evaluator:

```text
...........                                                              [100%]
11 passed in 0.49s
```

The tests prove concrete diagnostic output for:

- an ID switch on one physical tag from track 0 to track 1 at frame 1;
- a missed filtered movement event at its labeled interval-closing frame;
- a wrong detected class at frame 6, scored as both FP and FN;
- extra and missed events retaining source/closing frame information;
- notable-failure ranking in the Markdown renderer.

These are scripted verification examples, not results from the user's desk. No self-recorded files or hand-completed labels were available, so no real failure is claimed here.
