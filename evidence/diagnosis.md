# Phase 5 real-video failure diagnosis

> Diagnostic-only reconstruction from `data\evaluation\own_clips\desk_01.mp4` and `data\evaluation\own_clips\desk_01_labels\labels.json` because `evidence/real_video_report.md` was not present in the workspace. Labels SHA-256: `1dd7bf58fefb54cb9909349e91ccedb4a2e3e5ece999291b050bb916089754ac`. The existing evaluation chain and defaults were used unchanged (50 px matching tolerance; ConfidenceFilter threshold 0.35).

## Finding 1 — model output vocabulary versus ground truth

| Population | Classes | Can model output every labeled class? |
| --- | --- | --- |
| YOLO model (`yolov8n.pt`) | `person`, `bicycle`, `car`, `motorcycle`, `airplane`, `bus`, `train`, `truck`, `boat`, `traffic light`, `fire hydrant`, `stop sign`, `parking meter`, `bench`, `bird`, `cat`, `dog`, `horse`, `sheep`, `cow`, `elephant`, `bear`, `zebra`, `giraffe`, `backpack`, `umbrella`, `handbag`, `tie`, `suitcase`, `frisbee`, `skis`, `snowboard`, `sports ball`, `kite`, `baseball bat`, `baseball glove`, `skateboard`, `surfboard`, `tennis racket`, `bottle`, `wine glass`, `cup`, `fork`, `knife`, `spoon`, `bowl`, `banana`, `apple`, `sandwich`, `orange`, `broccoli`, `carrot`, `hot dog`, `pizza`, `donut`, `cake`, `chair`, `couch`, `potted plant`, `bed`, `dining table`, `toilet`, `tv`, `laptop`, `mouse`, `remote`, `keyboard`, `cell phone`, `microwave`, `oven`, `toaster`, `sink`, `refrigerator`, `book`, `clock`, `vase`, `scissors`, `teddy bear`, `hair drier`, `toothbrush` | n/a |
| `labels.json` ground truth | `bottle`, `wallet` | **no — unavailable: wallet** |

**Finding:** `wallet` is not in COCO/YOLOv8n's 80-class vocabulary, so all 60 wallet labels are impossible to classify correctly. `bottle` is available.

## Finding 2 — every false-positive detection

| Frame | FP type | Predicted class | Confidence | Box center | Nearest ground truth | Distance | Interpretation |
| ---: | --- | --- | ---: | --- | --- | ---: | --- |
| 0 | unmatched | `cup` | 0.4338 | `(719, 281)` | `bottle_1` (`bottle`) | 283.1px | phantom/background (no GT within 50px) |
| 30 | unmatched | `cup` | 0.5962 | `(719, 281)` | `bottle_1` (`bottle`) | 283.1px | phantom/background (no GT within 50px) |
| 60 | unmatched | `cup` | 0.5977 | `(719, 281)` | `bottle_1` (`bottle`) | 283.1px | phantom/background (no GT within 50px) |
| 90 | unmatched | `cup` | 0.6224 | `(718, 281)` | `bottle_1` (`bottle`) | 282.1px | phantom/background (no GT within 50px) |
| 120 | unmatched | `cup` | 0.6107 | `(718, 281)` | `bottle_1` (`bottle`) | 282.1px | phantom/background (no GT within 50px) |
| 150 | unmatched | `cup` | 0.5374 | `(717, 281)` | `bottle_1` (`bottle`) | 281.1px | phantom/background (no GT within 50px) |
| 180 | unmatched | `cup` | 0.5254 | `(714, 283)` | `bottle_1` (`bottle`) | 278.2px | phantom/background (no GT within 50px) |
| 210 | unmatched | `cup` | 0.3814 | `(712, 283)` | `bottle_1` (`bottle`) | 276.2px | phantom/background (no GT within 50px) |
| 240 | unmatched | `cup` | 0.4237 | `(711, 283)` | `bottle_1` (`bottle`) | 275.2px | phantom/background (no GT within 50px) |
| 270 | unmatched | `cup` | 0.4666 | `(711, 283)` | `bottle_1` (`bottle`) | 275.2px | phantom/background (no GT within 50px) |
| 330 | unmatched | `cup` | 0.5169 | `(711, 283)` | `bottle_1` (`bottle`) | 275.2px | phantom/background (no GT within 50px) |
| 360 | wrong class at GT | `cup` | 0.4974 | `(712, 282)` | `bottle_1` (`bottle`) | 8.5px | wrong class at a real object |
| 360 | unmatched | `person` | 0.6940 | `(745, 69)` | `bottle_1` (`bottle`) | 217.4px | phantom/background (no GT within 50px) |
| 390 | unmatched | `person` | 0.5667 | `(732, 80)` | `bottle_1` (`bottle`) | 212.0px | phantom/background (no GT within 50px) |
| 420 | unmatched | `person` | 0.5068 | `(539, 78)` | `bottle_1` (`bottle`) | 168.7px | phantom/background (no GT within 50px) |
| 450 | unmatched | `person` | 0.4693 | `(509, 93)` | `bottle_1` (`bottle`) | 192.9px | phantom/background (no GT within 50px) |
| 450 | unmatched | `person` | 0.4088 | `(620, 201)` | `bottle_1` (`bottle`) | 196.3px | phantom/background (no GT within 50px) |
| 780 | unmatched | `person` | 0.8325 | `(634, 194)` | `bottle_1` (`bottle`) | 212.2px | phantom/background (no GT within 50px) |
| 810 | unmatched | `person` | 0.8766 | `(563, 232)` | `bottle_1` (`bottle`) | 132.5px | phantom/background (no GT within 50px) |
| 840 | unmatched | `person` | 0.8713 | `(558, 232)` | `bottle_1` (`bottle`) | 127.8px | phantom/background (no GT within 50px) |
| 870 | unmatched | `person` | 0.8693 | `(559, 232)` | `bottle_1` (`bottle`) | 128.7px | phantom/background (no GT within 50px) |
| 900 | unmatched | `person` | 0.8710 | `(560, 232)` | `bottle_1` (`bottle`) | 129.7px | phantom/background (no GT within 50px) |
| 1080 | wrong class at GT | `cell phone` | 0.4052 | `(167, 405)` | `wallet_1` (`wallet`) | 2.0px | wrong class at a real object |
| 1080 | unmatched | `person` | 0.6597 | `(436, 179)` | `bottle_1` (`bottle`) | 94.0px | phantom/background (no GT within 50px) |
| 1110 | unmatched | `person` | 0.8052 | `(436, 210)` | `bottle_1` (`bottle`) | 63.0px | phantom/background (no GT within 50px) |
| 1140 | unmatched | `person` | 0.4429 | `(502, 210)` | `bottle_1` (`bottle`) | 90.5px | phantom/background (no GT within 50px) |
| 1410 | unmatched | `person` | 0.6111 | `(795, 316)` | `wallet_1` (`wallet`) | 162.8px | phantom/background (no GT within 50px) |
| 1440 | unmatched | `person` | 0.6423 | `(756, 309)` | `wallet_1` (`wallet`) | 183.4px | phantom/background (no GT within 50px) |
| 1470 | wrong class at GT | `cell phone` | 0.4944 | `(612, 434)` | `wallet_1` (`wallet`) | 14.1px | wrong class at a real object |
| 1470 | unmatched | `person` | 0.7373 | `(762, 303)` | `wallet_1` (`wallet`) | 191.8px | phantom/background (no GT within 50px) |
| 1770 | wrong class at GT | `cell phone` | 0.6173 | `(611, 434)` | `wallet_1` (`wallet`) | 14.0px | wrong class at a real object |
| 1770 | unmatched | `person` | 0.9148 | `(641, 212)` | `wallet_1` (`wallet`) | 210.3px | phantom/background (no GT within 50px) |
| 1800 | wrong class at GT | `cell phone` | 0.5128 | `(611, 435)` | `wallet_1` (`wallet`) | 15.0px | wrong class at a real object |
| 1800 | unmatched | `person` | 0.7367 | `(505, 199)` | `bottle_1` (`bottle`) | 100.5px | phantom/background (no GT within 50px) |
| 1830 | wrong class at GT | `cell phone` | 0.4376 | `(611, 434)` | `wallet_1` (`wallet`) | 14.0px | wrong class at a real object |
| 1830 | unmatched | `person` | 0.8422 | `(382, 197)` | `bottle_1` (`bottle`) | 93.8px | phantom/background (no GT within 50px) |
| 1860 | wrong class at GT | `cell phone` | 0.5123 | `(610, 433)` | `wallet_1` (`wallet`) | 13.0px | wrong class at a real object |
| 1860 | unmatched | `person` | 0.8683 | `(409, 209)` | `bottle_1` (`bottle`) | 69.9px | phantom/background (no GT within 50px) |

**Finding:** 38 detection FPs: 7 at a labeled object's location and 31 without a ground-truth object within 50 px.

## Finding 3 — every missed ground-truth object checked against raw detector output

| Frame | Ground truth | Center | Raw detector evidence within 50px | Diagnosis |
| ---: | --- | --- | --- | --- |
| 0 | `bottle_1` (`bottle`) | `(436, 272)` | none within 50px | (a) never detected |
| 0 | `wallet_1` (`wallet`) | `(165, 405)` | none within 50px | (a) never detected |
| 30 | `bottle_1` (`bottle`) | `(436, 272)` | none within 50px | (a) never detected |
| 30 | `wallet_1` (`wallet`) | `(165, 405)` | none within 50px | (a) never detected |
| 60 | `bottle_1` (`bottle`) | `(436, 272)` | none within 50px | (a) never detected |
| 60 | `wallet_1` (`wallet`) | `(165, 405)` | none within 50px | (a) never detected |
| 90 | `bottle_1` (`bottle`) | `(436, 272)` | none within 50px | (a) never detected |
| 90 | `wallet_1` (`wallet`) | `(165, 405)` | none within 50px | (a) never detected |
| 120 | `bottle_1` (`bottle`) | `(436, 272)` | none within 50px | (a) never detected |
| 120 | `wallet_1` (`wallet`) | `(165, 405)` | none within 50px | (a) never detected |
| 150 | `bottle_1` (`bottle`) | `(436, 272)` | none within 50px | (a) never detected |
| 150 | `wallet_1` (`wallet`) | `(165, 405)` | none within 50px | (a) never detected |
| 180 | `bottle_1` (`bottle`) | `(436, 272)` | none within 50px | (a) never detected |
| 180 | `wallet_1` (`wallet`) | `(165, 405)` | none within 50px | (a) never detected |
| 210 | `bottle_1` (`bottle`) | `(436, 272)` | none within 50px | (a) never detected |
| 210 | `wallet_1` (`wallet`) | `(165, 405)` | none within 50px | (a) never detected |
| 240 | `bottle_1` (`bottle`) | `(436, 272)` | none within 50px | (a) never detected |
| 240 | `wallet_1` (`wallet`) | `(165, 405)` | none within 50px | (a) never detected |
| 270 | `bottle_1` (`bottle`) | `(436, 272)` | none within 50px | (a) never detected |
| 270 | `wallet_1` (`wallet`) | `(165, 405)` | none within 50px | (a) never detected |
| 300 | `bottle_1` (`bottle`) | `(436, 272)` | none within 50px | (a) never detected |
| 300 | `wallet_1` (`wallet`) | `(165, 405)` | none within 50px | (a) never detected |
| 330 | `bottle_1` (`bottle`) | `(436, 272)` | none within 50px | (a) never detected |
| 330 | `wallet_1` (`wallet`) | `(165, 405)` | none within 50px | (a) never detected |
| 360 | `bottle_1` (`bottle`) | `(720, 285)` | cup conf=0.4974 center=(712, 282) distance=8.5px | (c) wrong class |
| 360 | `wallet_1` (`wallet`) | `(165, 405)` | none within 50px | (a) never detected |
| 390 | `bottle_1` (`bottle`) | `(682, 286)` | cup conf=0.3221 center=(679, 261) distance=25.2px | (c) wrong class |
| 390 | `wallet_1` (`wallet`) | `(165, 405)` | none within 50px | (a) never detected |
| 420 | `bottle_1` (`bottle`) | `(480, 236)` | none within 50px | (a) never detected |
| 420 | `wallet_1` (`wallet`) | `(165, 405)` | none within 50px | (a) never detected |
| 450 | `bottle_1` (`bottle`) | `(437, 272)` | cup conf=0.2674 center=(437, 265) distance=7.0px | (c) wrong class |
| 450 | `wallet_1` (`wallet`) | `(165, 405)` | none within 50px | (a) never detected |
| 480 | `bottle_1` (`bottle`) | `(437, 273)` | bottle conf=0.3462 center=(435, 274) distance=2.2px | (b) below ConfidenceFilter threshold |
| 480 | `wallet_1` (`wallet`) | `(165, 405)` | none within 50px | (a) never detected |
| 510 | `wallet_1` (`wallet`) | `(165, 405)` | none within 50px | (a) never detected |
| 540 | `wallet_1` (`wallet`) | `(165, 405)` | none within 50px | (a) never detected |
| 570 | `wallet_1` (`wallet`) | `(165, 405)` | none within 50px | (a) never detected |
| 600 | `wallet_1` (`wallet`) | `(165, 405)` | cell phone conf=0.2585 center=(168, 405) distance=3.0px | (c) wrong class |
| 630 | `wallet_1` (`wallet`) | `(165, 405)` | cell phone conf=0.2649 center=(168, 405) distance=3.0px | (c) wrong class |
| 660 | `wallet_1` (`wallet`) | `(165, 405)` | none within 50px | (a) never detected |
| 690 | `wallet_1` (`wallet`) | `(165, 405)` | none within 50px | (a) never detected |
| 720 | `wallet_1` (`wallet`) | `(165, 405)` | none within 50px | (a) never detected |
| 750 | `bottle_1` (`bottle`) | `(437, 273)` | bottle conf=0.3218 center=(435, 273) distance=2.0px | (b) below ConfidenceFilter threshold |
| 750 | `wallet_1` (`wallet`) | `(165, 405)` | none within 50px | (a) never detected |
| 780 | `bottle_1` (`bottle`) | `(437, 273)` | bottle conf=0.3161 center=(436, 273) distance=1.0px | (b) below ConfidenceFilter threshold |
| 780 | `wallet_1` (`wallet`) | `(165, 405)` | none within 50px | (a) never detected |
| 810 | `bottle_1` (`bottle`) | `(437, 273)` | none within 50px | (a) never detected |
| 810 | `wallet_1` (`wallet`) | `(165, 405)` | none within 50px | (a) never detected |
| 840 | `bottle_1` (`bottle`) | `(437, 273)` | none within 50px | (a) never detected |
| 840 | `wallet_1` (`wallet`) | `(165, 405)` | cell phone conf=0.2553 center=(167, 405) distance=2.0px | (c) wrong class |
| 870 | `bottle_1` (`bottle`) | `(437, 273)` | none within 50px | (a) never detected |
| 870 | `wallet_1` (`wallet`) | `(165, 405)` | none within 50px | (a) never detected |
| 900 | `bottle_1` (`bottle`) | `(437, 273)` | none within 50px | (a) never detected |
| 900 | `wallet_1` (`wallet`) | `(165, 405)` | none within 50px | (a) never detected |
| 930 | `bottle_1` (`bottle`) | `(437, 273)` | bottle conf=0.3199 center=(435, 273) distance=2.0px | (b) below ConfidenceFilter threshold |
| 930 | `wallet_1` (`wallet`) | `(165, 405)` | none within 50px | (a) never detected |
| 960 | `wallet_1` (`wallet`) | `(165, 405)` | none within 50px | (a) never detected |
| 990 | `wallet_1` (`wallet`) | `(165, 405)` | none within 50px | (a) never detected |
| 1020 | `wallet_1` (`wallet`) | `(165, 405)` | none within 50px | (a) never detected |
| 1050 | `wallet_1` (`wallet`) | `(165, 405)` | none within 50px | (a) never detected |
| 1080 | `bottle_1` (`bottle`) | `(437, 273)` | none within 50px | (a) never detected |
| 1080 | `wallet_1` (`wallet`) | `(165, 405)` | cell phone conf=0.4052 center=(167, 405) distance=2.0px | (c) wrong class |
| 1110 | `bottle_1` (`bottle`) | `(437, 273)` | none within 50px | (a) never detected |
| 1110 | `wallet_1` (`wallet`) | `(165, 405)` | none within 50px | (a) never detected |
| 1140 | `bottle_1` (`bottle`) | `(437, 273)` | none within 50px | (a) never detected |
| 1140 | `wallet_1` (`wallet`) | `(449, 125)` | none within 50px | (a) never detected |
| 1170 | `bottle_1` (`bottle`) | `(437, 273)` | bottle conf=0.2875 center=(435, 273) distance=2.0px | (b) below ConfidenceFilter threshold |
| 1200 | `bottle_1` (`bottle`) | `(437, 273)` | none within 50px | (a) never detected |
| 1230 | `bottle_1` (`bottle`) | `(437, 273)` | bottle conf=0.2841 center=(435, 273) distance=2.0px | (b) below ConfidenceFilter threshold |
| 1260 | `bottle_1` (`bottle`) | `(437, 273)` | bottle conf=0.2705 center=(435, 273) distance=2.0px | (b) below ConfidenceFilter threshold |
| 1290 | `bottle_1` (`bottle`) | `(437, 273)` | bottle conf=0.3272 center=(435, 273) distance=2.0px | (b) below ConfidenceFilter threshold |
| 1320 | `bottle_1` (`bottle`) | `(437, 273)` | bottle conf=0.2677 center=(435, 273) distance=2.0px | (b) below ConfidenceFilter threshold |
| 1350 | `bottle_1` (`bottle`) | `(437, 273)` | bottle conf=0.3111 center=(435, 273) distance=2.0px | (b) below ConfidenceFilter threshold |
| 1380 | `bottle_1` (`bottle`) | `(437, 273)` | bottle conf=0.2582 center=(435, 273) distance=2.0px | (b) below ConfidenceFilter threshold |
| 1410 | `bottle_1` (`bottle`) | `(437, 273)` | none within 50px | (a) never detected |
| 1410 | `wallet_1` (`wallet`) | `(650, 390)` | none within 50px | (a) never detected |
| 1440 | `bottle_1` (`bottle`) | `(437, 273)` | bottle conf=0.3173 center=(435, 273) distance=2.0px | (b) below ConfidenceFilter threshold |
| 1440 | `wallet_1` (`wallet`) | `(610, 420)` | cell phone conf=0.3123 center=(625, 420) distance=15.0px | (c) wrong class |
| 1470 | `bottle_1` (`bottle`) | `(437, 273)` | bottle conf=0.3154 center=(435, 273) distance=2.0px | (b) below ConfidenceFilter threshold |
| 1470 | `wallet_1` (`wallet`) | `(610, 420)` | cell phone conf=0.4944 center=(612, 434) distance=14.1px | (c) wrong class |
| 1500 | `bottle_1` (`bottle`) | `(437, 273)` | bottle conf=0.3367 center=(435, 273) distance=2.0px | (b) below ConfidenceFilter threshold |
| 1500 | `wallet_1` (`wallet`) | `(610, 420)` | none within 50px | (a) never detected |
| 1530 | `wallet_1` (`wallet`) | `(610, 420)` | none within 50px | (a) never detected |
| 1560 | `wallet_1` (`wallet`) | `(610, 420)` | none within 50px | (a) never detected |
| 1590 | `bottle_1` (`bottle`) | `(437, 273)` | bottle conf=0.3468 center=(435, 273) distance=2.0px | (b) below ConfidenceFilter threshold |
| 1590 | `wallet_1` (`wallet`) | `(610, 420)` | none within 50px | (a) never detected |
| 1620 | `bottle_1` (`bottle`) | `(437, 273)` | bottle conf=0.3385 center=(435, 272) distance=2.2px | (b) below ConfidenceFilter threshold |
| 1620 | `wallet_1` (`wallet`) | `(610, 420)` | none within 50px | (a) never detected |
| 1650 | `bottle_1` (`bottle`) | `(437, 273)` | bottle conf=0.3333 center=(435, 273) distance=2.0px | (b) below ConfidenceFilter threshold |
| 1650 | `wallet_1` (`wallet`) | `(610, 420)` | none within 50px | (a) never detected |
| 1680 | `wallet_1` (`wallet`) | `(610, 420)` | none within 50px | (a) never detected |
| 1710 | `wallet_1` (`wallet`) | `(610, 420)` | none within 50px | (a) never detected |
| 1740 | `bottle_1` (`bottle`) | `(437, 273)` | bottle conf=0.2926 center=(435, 273) distance=2.0px | (b) below ConfidenceFilter threshold |
| 1740 | `wallet_1` (`wallet`) | `(610, 420)` | none within 50px | (a) never detected |
| 1770 | `bottle_1` (`bottle`) | `(437, 273)` | none within 50px | (a) never detected |
| 1770 | `wallet_1` (`wallet`) | `(610, 420)` | cell phone conf=0.6173 center=(611, 434) distance=14.0px | (c) wrong class |
| 1800 | `bottle_1` (`bottle`) | `(437, 273)` | none within 50px | (a) never detected |
| 1800 | `wallet_1` (`wallet`) | `(610, 420)` | cell phone conf=0.5128 center=(611, 435) distance=15.0px | (c) wrong class |
| 1830 | `bottle_1` (`bottle`) | `(437, 273)` | none within 50px | (a) never detected |
| 1830 | `wallet_1` (`wallet`) | `(610, 420)` | cell phone conf=0.4376 center=(611, 434) distance=14.0px | (c) wrong class |
| 1860 | `bottle_1` (`bottle`) | `(437, 273)` | none within 50px | (a) never detected |
| 1860 | `wallet_1` (`wallet`) | `(610, 420)` | cell phone conf=0.5123 center=(610, 433) distance=13.0px | (c) wrong class |
| 1890 | `bottle_1` (`bottle`) | `(437, 273)` | bottle conf=0.2933 center=(435, 272) distance=2.2px | (b) below ConfidenceFilter threshold |
| 1890 | `wallet_1` (`wallet`) | `(610, 420)` | none within 50px | (a) never detected |
| 1920 | `bottle_1` (`bottle`) | `(437, 273)` | bottle conf=0.3419 center=(435, 272) distance=2.2px | (b) below ConfidenceFilter threshold |
| 1920 | `wallet_1` (`wallet`) | `(610, 420)` | none within 50px | (a) never detected |
| 1950 | `wallet_1` (`wallet`) | `(610, 420)` | none within 50px | (a) never detected |
| 1980 | `wallet_1` (`wallet`) | `(610, 420)` | none within 50px | (a) never detected |
| 2010 | `wallet_1` (`wallet`) | `(610, 420)` | none within 50px | (a) never detected |

| Miss category | Count |
| --- | ---: |
| (a) never detected | 76 |
| (b) below ConfidenceFilter threshold | 20 |
| (c) wrong class | 13 |

Raw means the adapter output immediately after `VisionDetector.detect` and before `ConfidenceFilter`; YOLO's own default prediction floor still applies.

## Finding 4 — the 10 track-ID switches

| Switch frame | Ground-truth tag | Track switch | Old track last observed | New track first observed | Old track `missed_frames` leading up to replacement | GT present during gap? | Exact FP event pair? | Cause |
| ---: | --- | --- | ---: | ---: | --- | --- | --- | --- |
| 510 | `bottle_1` | 0 → 14 | 374 | 498 | f375:1, f376:2, f377:3, f378:4, f379:5 | labeled checkpoints: 390, 420, 450, 480, 510 | no | detection gap; old track reached timeout |
| 960 | `bottle_1` | 14 → 22 | 748 | 934 | f749:1, f750:2, f751:3, f752:4, f753:5 | labeled checkpoints: 750, 780, 810, 840, 870, 900, 930, 960 | no | detection gap; old track reached timeout |
| 1470 | `wallet_1` | 26 → 33 | 1084 | 1469 | f1085:1, f1086:2, f1087:3, f1088:4, f1089:5 | labeled checkpoints: 1110, 1140, 1410, 1440, 1470 | no | detection gap; old track reached timeout |
| 1530 | `bottle_1` | 22 → 36 | 1053 | 1527 | f1054:1, f1055:2, f1056:3, f1057:4, f1058:5 | labeled checkpoints: 1080, 1110, 1140, 1170, 1200, 1230, 1260, 1290, 1320, 1350, 1380, 1410, 1440, 1470, 1500, 1530 | no | detection gap; old track reached timeout |
| 1560 | `bottle_1` | 36 → 37 | 1537 | 1560 | f1538:1, f1539:2, f1540:3, f1541:4, f1542:5 | labeled checkpoints: 1560 | yes | detection gap; old track reached timeout |
| 1680 | `bottle_1` | 37 → 44 | 1560 | 1672 | f1561:1, f1562:2, f1563:3, f1564:4, f1565:5 | labeled checkpoints: 1590, 1620, 1650, 1680 | no | detection gap; old track reached timeout |
| 1710 | `bottle_1` | 44 → 45 | 1686 | 1693 | f1687:1, f1688:2, f1689:3, f1690:4, f1691:5 | labeled checkpoints: 1710 | yes | detection gap; old track reached timeout |
| 1770 | `wallet_1` | 33 → 50 | 1481 | 1747 | f1482:1, f1483:2, f1484:3, f1485:4, f1486:5 | labeled checkpoints: 1500, 1530, 1560, 1590, 1620, 1650, 1680, 1710, 1740, 1770 | no | detection gap; old track reached timeout |
| 1950 | `bottle_1` | 45 → 62 | 1714 | 1937 | f1715:1, f1716:2, f1717:3, f1718:4, f1719:5 | labeled checkpoints: 1740, 1770, 1800, 1830, 1860, 1890, 1920, 1950 | no | detection gap; old track reached timeout |
| 1980 | `bottle_1` | 62 → 65 | 1951 | 1978 | f1952:1, f1953:2, f1954:3, f1955:4, f1956:5 | labeled checkpoints: 1980 | yes | detection gap; old track reached timeout |

Ground-truth presence can only be asserted at the hand-labeled 30-frame checkpoints; it is not interpolated across unlabeled video frames.

## Finding 5 — event false positives cross-referenced with ID switches

| Event-FP population | Count |
| --- | ---: |
| All event false positives | 217 |
| FP events belonging to an old-track `DISAPPEARED` + new-track `APPEARED` pair for the 10 exact switched track IDs | 20 (10 pairs) |
| Of those, FP events whose complete pair falls in the same labeled interval ending at the switch checkpoint | 6 (3 pairs) |
| FP events with no corresponding switched-track lifecycle pair | 197 |

The primary cross-reference follows the exact old/new track IDs, even when the old track timed out in an earlier 30-frame evaluation interval and the replacement first appeared later. Every switch has both lifecycle FPs, so the 10 switches explain 20 of 217 event FPs. The stricter same-interval view explains only 6 FPs (the switches at checkpoints 1560, 1710, and 1980). Each pair's two constituent event FPs are counted separately.

## Finding 6 — detection TP=19 versus identity denominator=26

| Metric | Population | Observed count | Why it differs |
| --- | --- | ---: | --- |
| Detected-object TP | Filtered detections spatially matched one-to-one to GT within 50 px **and** class-correct | 19 | Wrong-class spatial matches are not TPs; each becomes one detection FP plus one detection FN. |
| Identity denominator | GT objects spatially matched one-to-one to a currently observed track (`missed_frames == 0`) within 50 px, regardless of class correctness | 26 | It tests the resolved identity on every spatial track match, so wrong-class matches remain in the denominator. |
| Difference | Spatially matched tracked objects that were not class-correct detection TPs | 7 | These account for the denominator gap. |

Reconstructed consistency totals: detection `tp=19, fp=38, fn=109`; identity `19/26`; switches `10`; event FPs `217`.
