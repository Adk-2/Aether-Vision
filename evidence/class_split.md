# Phase 5a real-video metrics by ground-truth class

> Diagnostic-only rerun of `evaluation.real_video_eval` against `data/evaluation/own_clips/desk_01.mp4` and its completed `labels.json`, using `yolov8n.pt`, the evaluator's 50 px greedy one-to-one matching, and its unchanged pipeline defaults.

## Model vocabulary and OOV confirmation

| Item | Result |
| --- | --- |
| Actual model class list (80 classes) | `person`, `bicycle`, `car`, `motorcycle`, `airplane`, `bus`, `train`, `truck`, `boat`, `traffic light`, `fire hydrant`, `stop sign`, `parking meter`, `bench`, `bird`, `cat`, `dog`, `horse`, `sheep`, `cow`, `elephant`, `bear`, `zebra`, `giraffe`, `backpack`, `umbrella`, `handbag`, `tie`, `suitcase`, `frisbee`, `skis`, `snowboard`, `sports ball`, `kite`, `baseball bat`, `baseball glove`, `skateboard`, `surfboard`, `tennis racket`, `bottle`, `wine glass`, `cup`, `fork`, `knife`, `spoon`, `bowl`, `banana`, `apple`, `sandwich`, `orange`, `broccoli`, `carrot`, `hot dog`, `pizza`, `donut`, `cake`, `chair`, `couch`, `potted plant`, `bed`, `dining table`, `toilet`, `tv`, `laptop`, `mouse`, `remote`, `keyboard`, `cell phone`, `microwave`, `oven`, `toaster`, `sink`, `refrigerator`, `book`, `clock`, `vase`, `scissors`, `teddy bear`, `hair drier`, `toothbrush` |
| Is `wallet` present? | **No** |
| Nearest available COCO class for the labeled object | `handbag` (YOLO model class index 26); this is a semantic observation only, not a relabel or mapping used in scoring |

`wallet` is out of vocabulary for this checkpoint. The list does contain `handbag`, but the evaluator continues to compare the hand-written `wallet` label literally; no remapping was applied.

## Class-split metrics

| Ground-truth class | GT instances | Detection TP | Class-attributed FP | FN | Detection precision | Detection recall | Identity correct / compared | Identity accuracy | ID switches |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `bottle` | 68 | 19 | 1 | 49 | 95.00% (19/20) | 27.94% (19/68) | 19/20 | 95.00% | 8 |
| `wallet` | 60 | 0 | 6 | 60 | 0.00% (0/6) | 0.00% (0/60) | 0/6 | 0.00% | 2 |

A false positive is attributed to a ground-truth class only for the evaluator's spatially matched wrong-class case. The 31 unmatched prediction FPs have no ground-truth class and remain in a separate background/unattributed bucket. This preserves the pooled evaluator arithmetic instead of assigning background predictions to whichever labeled object happens to be nearest.

| Precision reconciliation | TP | FP | Precision |
| --- | ---: | ---: | ---: |
| `bottle`-attributed | 19 | 1 | 95.00% |
| `wallet`-attributed | 0 | 6 | 0.00% |
| Unmatched/background predictions | 0 | 31 | 0.00% |
| Pooled evaluator | 19 | 38 | 33.33% |

## False-negative and ID-switch shares

| Ground-truth class | False negatives | Share of pooled FN=109 | ID switches | Share of pooled switches=10 |
| --- | ---: | ---: | ---: | ---: |
| `bottle` | 49 | 44.95% | 8 | 80.00% |
| `wallet` | 60 | 55.05% | 2 | 20.00% |
| Total | 109 | 100.00% | 10 | 100.00% |

## Reconciliation

| Check | Result |
| --- | --- |
| Detection TP | 19 + 0 = 19 (pooled: 19) |
| Detection FP | 1 + 6 wrong-class-at-GT + 31 unmatched = 38 (pooled: 38) |
| Detection FN | 49 + 60 = 109 (pooled: 109) |
| Identity comparisons | 20 + 6 = 26 (pooled: 26) |
| ID switches | 8 + 2 = 10 (pooled: 10) |

The OOV gap directly forces all 60 wallet instances to be detection false negatives under literal class matching. Six wallet locations nevertheless had a spatially matched observed track, but its label was not `wallet`, producing identity accuracy 0/6. No labels or model outputs were altered.
