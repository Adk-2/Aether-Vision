# Phase 5c step 2 — corrected-label bottle threshold sweep

> Measurement only. No detector, tracker, timeout, identity, event-engine, model, or production-threshold settings were changed. Raw output means `VisionDetector.detect` converted by `DetectionAdapter`, before the production `ConfidenceFilter`; “nothing” is therefore relative to YOLO's internal prediction floor. Matching uses the evaluator's 50 px one-to-one nearest-center rule. Corrected-label SHA-256: `9f0337dbfeb16ba7d0cf988b3aea3ba9184d479322d3787472e1dfbdb0b1421b`.

## 1. Raw detector output at the 12 corrected centers

| Frame | Corrected bottle GT center | Diagnosis | Nearest raw detector output within 50 px |
| ---: | --- | --- | --- |
| 0 | `(720, 281)` | wrong-class | `cup`, confidence 0.4338, center `(719, 281)`, distance 1.0 px |
| 30 | `(720, 281)` | wrong-class | `cup`, confidence 0.5962, center `(719, 281)`, distance 1.0 px |
| 60 | `(720, 281)` | wrong-class | `cup`, confidence 0.5977, center `(719, 281)`, distance 1.0 px |
| 90 | `(720, 281)` | wrong-class | `cup`, confidence 0.6224, center `(718, 281)`, distance 2.0 px |
| 120 | `(720, 281)` | wrong-class | `cup`, confidence 0.6107, center `(718, 281)`, distance 2.0 px |
| 150 | `(719, 281)` | wrong-class | `cup`, confidence 0.5374, center `(717, 281)`, distance 2.0 px |
| 180 | `(715, 283)` | wrong-class | `cup`, confidence 0.5254, center `(714, 283)`, distance 1.0 px |
| 210 | `(714, 284)` | wrong-class | `cup`, confidence 0.3814, center `(712, 283)`, distance 2.2 px |
| 240 | `(713, 284)` | wrong-class | `cup`, confidence 0.4237, center `(711, 283)`, distance 2.2 px |
| 270 | `(713, 284)` | wrong-class and below-threshold (distance tie) | `cup`, confidence 0.4666, and `bottle`, confidence 0.2924; both center `(711, 283)`, distance 2.2 px |
| 300 | `(713, 284)` | wrong-class | `cup`, confidence 0.3381, center `(711, 283)`, distance 2.2 px |
| 330 | `(713, 284)` | below-threshold | `bottle`, confidence 0.2832, center `(712, 283)`, distance 1.4 px |

Frame 180 also has a `vase` output at confidence 0.2578, center `(714, 282)`, distance 1.4 px. Frame 330 also has a `cup` output at confidence 0.5169, center `(711, 283)`, distance 2.2 px. These are not the nearest raw outputs, but they matter to the production-threshold explanation below.

### Why pooled detection remains 19/38/109

The corrected-label pooled detection result was reproduced as **TP 19, FP 38, FN 109**, identical to the pre-correction result. This invariance is explained by the detection scorer itself, not by identity matching and not by an absence of raw output near the corrected centers.

At the unchanged 0.35 production threshold, frames 0–270 have a nearby `cup` output above threshold, frame 300 has no nearby output surviving the threshold (`cup` is 0.3381), and frame 330 has a nearby `cup` output above threshold. Thus the 12 corrected frames contribute 11 wrong-class cases plus one unmatched GT.

- Before correction, each of those 11 `cup` predictions was far from the old bottle GT center. Each frame therefore contributed one unmatched-prediction FP and one unmatched-GT FN. Frame 300 contributed only one FN.
- After correction, each of the 11 `cup` predictions spatially matches the bottle GT. The evaluator explicitly scores a spatially matched wrong class as one FP plus one FN. Frame 300 still contributes only one FN.

The segment therefore contributes the same 11 FP and 12 FN before and after correction, with no new TP at 0.35. That preserves the pooled 19/38/109 totals.

Detection and identity scoring are separate. Detection TP/FP/FN uses the post-`ConfidenceFilter` `detections` list directly. Identity scoring independently selects currently observed tracks (`missed_frames == 0`) and spatially matches each track's `current_detection.center` to GT. The latter can change identity coverage after a coordinate correction, but it does not produce or explain the pooled detection counts.

## 2. Bottle-only threshold sweep on corrected labels

For each threshold, only normalized `bottle` predictions are matched one-to-one to the 68 bottle GT instances. An unmatched bottle prediction is a bottle FP; wrong-class predictions such as `cup` are outside this class-specific sweep. Precision is `TP / (TP + FP)` and recall is `TP / 68`.

| Confidence threshold | Bottle TP | Bottle FP | Bottle FN | Precision | Recall | Delta TP vs 0.35 | Delta FP vs 0.35 |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| **0.35 (production)** | 19 | 0 | 49 | 100.00% | 27.94% | +0 | +0 |
| 0.32 | 27 | 0 | 41 | 100.00% | 39.71% | +8 | +0 |
| 0.30 | 32 | 0 | 36 | 100.00% | 47.06% | +13 | +0 |
| 0.28 | 38 | 0 | 30 | 100.00% | 55.88% | +19 | +0 |
| 0.25 | 41 | 0 | 27 | 100.00% | 60.29% | +22 | +0 |

The label correction turns the old bottle FPs at frames 270 and 330 into spatial matches at thresholds 0.28 and 0.25. Consequently, the corrected sweep has zero bottle FP at every tested threshold.

## 3. Frames 270 and 330

Both earlier “nothing detected” diagnoses are resolved at the raw-output level after moving the GT centers onto the visible bottle:

- **Frame 270:** raw `bottle` confidence 0.2924 at `(711, 283)`, 2.2 px from corrected GT `(713, 284)`. A `cup` at confidence 0.4666 is tied at the same center and distance. At production threshold 0.35 this remains a detection FN through a wrong-class match; in the bottle-only sweep it becomes a TP at 0.28 and 0.25.
- **Frame 330:** raw `bottle` confidence 0.2832 at `(712, 283)`, 1.4 px from corrected GT `(713, 284)`. A `cup` at confidence 0.5169 is 2.2 px away. At production threshold 0.35 this remains a detection FN through the surviving wrong-class match; in the bottle-only sweep it becomes a TP at 0.28 and 0.25.

So the coordinate correction resolves the claim that the detector produced nothing near these two bottles, and the tested 0.28/0.25 bottle-only thresholds resolve both as bottle TPs. It does not resolve either FN under the unchanged 0.35 production threshold.
