# Event jitter fix

Command: `python -m evaluation.event_sweep`; full output: event-sweep.md.

Sweep ran before choosing the default. Selected min_pixels=1, fraction=0: smallest effective tested threshold that eliminates every jitter pair without losing any hand-authored real move/start. This is tuned on synthetic data, not validated as a production optimum. All fixture boxes are 10x10; nonzero fractional defaults are not justified by that single scale. The implementation supports max(min_pixels, fraction * current bbox diagonal), strict greater-than, Euclidean center displacement from the previous frame. The zero/zero configuration reproduces the old behavior.

No event ground truth changed. Stop count still resets on ANY center change, including suppressed jitter, as specified in Phase 2c A.1. Consequently slow movement made entirely of subthreshold frame-to-frame changes can be suppressed; this limitation is not hidden by these fixtures.

Jitter annotations now identify track IDs at each frame; numerator counts annotated (frame, track) pairs with any movement/stop event on that track, denominator counts annotated pairs. A different track's genuine move or stop cannot count against the jitter track. Recomputed old-policy baselines remain raw 8/8 and filtered 1/2, so the saved before.md numbers happen to be numerically comparable despite the corrected definition. Regression tests exercise two tracks in one frame.

Phase 2c tests that intentionally demonstrate old jitter mismatches now explicitly use EventPolicy(min_pixels=0), preserving their mismatch-reporting and oracle-sensitivity purpose. New tests verify default jitter rejection, real-move retention, strict boundary, diagonal scaling, and invalid policy parameters.

Verification: 81 tests and 6 subtests passed (event-pytest.txt). Both event scenarios now have 100% precision/recall/F1, zero jitter pairs emitting movement, and zero real moves missed (event-evaluation.md).
