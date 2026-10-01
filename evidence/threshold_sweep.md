# Phase 5c ground-truth review and bottle threshold sweep

> Diagnostic-only output. No labels, pipeline code, tracker code, thresholds, or model settings were changed. The 12 review images are full-frame copies of the existing extracted annotation frames, despite the directory name `gt_review_crops`.

## 1. Ground-truth review: labeled frames 0–330

All 12 frames visibly contain the bottle near the far-right side of the image. The current ground-truth center `(436, 272)` lies near the middle of the image and is not on the bottle. This is consistent across the entire 0–330 segment. The images are provided for manual review only; `labels.json` was not edited.

| Frame | Current bottle GT center | Full-frame review image | Visual check |
| ---: | --- | --- | --- |
| 0 | `(436, 272)` | [frame_000000.jpg](gt_review_crops/frame_000000.jpg) | Bottle visible at far right; labeled center is not on it |
| 30 | `(436, 272)` | [frame_000030.jpg](gt_review_crops/frame_000030.jpg) | Bottle visible at far right; labeled center is not on it |
| 60 | `(436, 272)` | [frame_000060.jpg](gt_review_crops/frame_000060.jpg) | Bottle visible at far right; labeled center is not on it |
| 90 | `(436, 272)` | [frame_000090.jpg](gt_review_crops/frame_000090.jpg) | Bottle visible at far right; labeled center is not on it |
| 120 | `(436, 272)` | [frame_000120.jpg](gt_review_crops/frame_000120.jpg) | Bottle visible at far right; labeled center is not on it |
| 150 | `(436, 272)` | [frame_000150.jpg](gt_review_crops/frame_000150.jpg) | Bottle visible at far right; labeled center is not on it |
| 180 | `(436, 272)` | [frame_000180.jpg](gt_review_crops/frame_000180.jpg) | Bottle visible at far right; labeled center is not on it |
| 210 | `(436, 272)` | [frame_000210.jpg](gt_review_crops/frame_000210.jpg) | Bottle visible at far right; labeled center is not on it |
| 240 | `(436, 272)` | [frame_000240.jpg](gt_review_crops/frame_000240.jpg) | Bottle visible at far right; labeled center is not on it |
| 270 | `(436, 272)` | [frame_000270.jpg](gt_review_crops/frame_000270.jpg) | Bottle visible at far right; labeled center is not on it |
| 300 | `(436, 272)` | [frame_000300.jpg](gt_review_crops/frame_000300.jpg) | Bottle visible at far right; labeled center is not on it |
| 330 | `(436, 272)` | [frame_000330.jpg](gt_review_crops/frame_000330.jpg) | Bottle visible at far right; labeled center is not on it |

This review strongly supports an annotation-position error across these 12 frames. It does not establish replacement coordinates; those remain for manual labeling review.

## 2. Bottle confidence-threshold precision sweep

The sweep decodes the labeled frames directly from `desk_01.mp4`, matching the evaluator's input path. For each threshold, it keeps predictions normalized to class `bottle` and greedily matches them one-to-one to bottle ground truth within the evaluator's 50 px tolerance. Precision is `TP / (TP + FP)` and recall is `TP / 68`. Wrong-class outputs such as `cup` are excluded from this class-specific precision calculation; unmatched predicted `bottle` instances are false positives.

| Confidence threshold | Bottle predictions | TP | FP | FN | Bottle precision | Bottle recall | TP gain vs 0.35 | FP gain vs 0.35 |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| **0.35 (current)** | 19 | 19 | 0 | 49 | **100.00%** | **27.94%** | — | — |
| 0.32 | 27 | 27 | 0 | 41 | 100.00% | 39.71% | +8 | +0 |
| 0.30 | 32 | 32 | 0 | 36 | 100.00% | 47.06% | +13 | +0 |
| 0.28 | 38 | 36 | 2 | 32 | 94.74% | 52.94% | +17 | +2 |
| 0.25 | 41 | 39 | 2 | 29 | 95.12% | 57.35% | +20 | +2 |

| Threshold step | Newly recovered bottle TPs | Newly introduced bottle FPs | FP frames introduced at this step |
| --- | ---: | ---: | --- |
| 0.35 → 0.32 | 8 | 0 | none |
| 0.32 → 0.30 | 5 | 0 | none |
| 0.30 → 0.28 | 4 | 2 | 270 and 330 |
| 0.28 → 0.25 | 3 | 0 | none |

The two bottle FPs at thresholds 0.28 and 0.25 are not background hallucinations: they are predictions centered at approximately `(711, 283)` in frame 270 and `(712, 283)` in frame 330, on the visibly present bottle. They score as FPs only because the current ground truth remains at `(436, 272)`, more than 50 px away. Therefore the apparent precision loss at 0.28 is entangled with the annotation-position issue identified above.

Within the labels as currently written, lowering from 0.35 to 0.30 raises bottle recall from 27.94% to 47.06% with no added bottle-class FPs. At 0.28 the measured recall reaches 52.94%, while the only two FPs are both tied to the suspect early-frame coordinates. This remains diagnostic evidence, not a recommendation to change the threshold before the ground truth is manually reviewed.
