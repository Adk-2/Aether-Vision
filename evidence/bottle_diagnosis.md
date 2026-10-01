# Phase 5b bottle-only detection and tracking diagnosis

> Scope is restricted to the 68 `bottle` ground-truth instances and the eight bottle-tagged ID switches from Phase 5a. `wallet` is excluded. Raw detections are adapter output immediately after `VisionDetector.detect` and before the 0.35 `ConfidenceFilter`; YOLO's internal default prediction floor still applies, so “nothing” means no raw model output within the evaluator's 50 px radius at or above that internal floor.

## Finding 1 — all 49 bottle false negatives

| Raw-output diagnosis | Count | Share of 49 bottle FNs |
| --- | ---: | ---: |
| (a) Nothing detected within 50 px | 26 | 53.06% |
| (b) Correct `bottle` below the 0.35 confidence threshold | 20 | 40.82% |
| (c) Different class within 50 px | 3 | 6.12% |
| Total | 49 | 100.00% |

| Frame | GT center | Category | Nearest raw detector output within 50 px |
| ---: | --- | --- | --- |
| 0 | `(436, 272)` | (a) nothing | none |
| 30 | `(436, 272)` | (a) nothing | none |
| 60 | `(436, 272)` | (a) nothing | none |
| 90 | `(436, 272)` | (a) nothing | none |
| 120 | `(436, 272)` | (a) nothing | none |
| 150 | `(436, 272)` | (a) nothing | none |
| 180 | `(436, 272)` | (a) nothing | none |
| 210 | `(436, 272)` | (a) nothing | none |
| 240 | `(436, 272)` | (a) nothing | none |
| 270 | `(436, 272)` | (a) nothing | none |
| 300 | `(436, 272)` | (a) nothing | none |
| 330 | `(436, 272)` | (a) nothing | none |
| 360 | `(720, 285)` | (c) different class | `cup`, confidence 0.4974, center `(712, 282)`, distance 8.5 px |
| 390 | `(682, 286)` | (c) different class | `cup`, confidence 0.3221, center `(679, 261)`, distance 25.2 px |
| 420 | `(480, 236)` | (a) nothing | none |
| 450 | `(437, 272)` | (c) different class | `cup`, confidence 0.2674, center `(437, 265)`, distance 7.0 px |
| 480 | `(437, 273)` | (b) below threshold | `bottle`, confidence 0.3462, center `(435, 274)`, distance 2.2 px |
| 750 | `(437, 273)` | (b) below threshold | `bottle`, confidence 0.3218, center `(435, 273)`, distance 2.0 px |
| 780 | `(437, 273)` | (b) below threshold | `bottle`, confidence 0.3161, center `(436, 273)`, distance 1.0 px |
| 810 | `(437, 273)` | (a) nothing | none |
| 840 | `(437, 273)` | (a) nothing | none |
| 870 | `(437, 273)` | (a) nothing | none |
| 900 | `(437, 273)` | (a) nothing | none |
| 930 | `(437, 273)` | (b) below threshold | `bottle`, confidence 0.3199, center `(435, 273)`, distance 2.0 px |
| 1080 | `(437, 273)` | (a) nothing | none |
| 1110 | `(437, 273)` | (a) nothing | none |
| 1140 | `(437, 273)` | (a) nothing | none |
| 1170 | `(437, 273)` | (b) below threshold | `bottle`, confidence 0.2875, center `(435, 273)`, distance 2.0 px |
| 1200 | `(437, 273)` | (a) nothing | none |
| 1230 | `(437, 273)` | (b) below threshold | `bottle`, confidence 0.2841, center `(435, 273)`, distance 2.0 px |
| 1260 | `(437, 273)` | (b) below threshold | `bottle`, confidence 0.2705, center `(435, 273)`, distance 2.0 px |
| 1290 | `(437, 273)` | (b) below threshold | `bottle`, confidence 0.3272, center `(435, 273)`, distance 2.0 px |
| 1320 | `(437, 273)` | (b) below threshold | `bottle`, confidence 0.2677, center `(435, 273)`, distance 2.0 px |
| 1350 | `(437, 273)` | (b) below threshold | `bottle`, confidence 0.3111, center `(435, 273)`, distance 2.0 px |
| 1380 | `(437, 273)` | (b) below threshold | `bottle`, confidence 0.2582, center `(435, 273)`, distance 2.0 px |
| 1410 | `(437, 273)` | (a) nothing | none |
| 1440 | `(437, 273)` | (b) below threshold | `bottle`, confidence 0.3173, center `(435, 273)`, distance 2.0 px |
| 1470 | `(437, 273)` | (b) below threshold | `bottle`, confidence 0.3154, center `(435, 273)`, distance 2.0 px |
| 1500 | `(437, 273)` | (b) below threshold | `bottle`, confidence 0.3367, center `(435, 273)`, distance 2.0 px |
| 1590 | `(437, 273)` | (b) below threshold | `bottle`, confidence 0.3468, center `(435, 273)`, distance 2.0 px |
| 1620 | `(437, 273)` | (b) below threshold | `bottle`, confidence 0.3385, center `(435, 272)`, distance 2.2 px |
| 1650 | `(437, 273)` | (b) below threshold | `bottle`, confidence 0.3333, center `(435, 273)`, distance 2.0 px |
| 1740 | `(437, 273)` | (b) below threshold | `bottle`, confidence 0.2926, center `(435, 273)`, distance 2.0 px |
| 1770 | `(437, 273)` | (a) nothing | none |
| 1800 | `(437, 273)` | (a) nothing | none |
| 1830 | `(437, 273)` | (a) nothing | none |
| 1860 | `(437, 273)` | (a) nothing | none |
| 1890 | `(437, 273)` | (b) below threshold | `bottle`, confidence 0.2933, center `(435, 272)`, distance 2.2 px |
| 1920 | `(437, 273)` | (b) below threshold | `bottle`, confidence 0.3419, center `(435, 272)`, distance 2.2 px |

Representative GT-centered crops from category (a):

| Frame | Crop | Visual reason to inspect |
| ---: | --- | --- |
| 0 | [GT-centered crop](bottle_diagnosis_crops/bottle_frame_000000_gt_crop.jpg) | The labeled center contains empty wall/table while the visible bottle is far to the right in the full frame. This suggests a ground-truth position mismatch for the early static segment, not merely a detector miss. |
| 420 | [GT-centered crop](bottle_diagnosis_crops/bottle_frame_000420_gt_crop.jpg) | Bottle is suspended and grasped at the cap, changing its silhouette/context. |
| 810 | [GT-centered crop](bottle_diagnosis_crops/bottle_frame_000810_gt_crop.jpg) | Bottle is visible, but its lower portion is occluded by the hand/forearm. |
| 1800 | [GT-centered crop](bottle_diagnosis_crops/bottle_frame_001800_gt_crop.jpg) | Bottle is visible with the arm/hand crossing its upper-left region. |

The frame-0 observation also applies to labeled frames 0–330: all use center `(436, 272)`, while the visible bottle is on the right side of the image. Those 12 “nothing” rows should therefore not be interpreted as pure detector-recall failures without first validating the annotations.

## Finding 2 — eight bottle-tagged ID switches

`I` means the old track was already inactive. The immediate-window column explicitly prints the old track's stored `missed_frames` for each of the ten frames before the labeled switch checkpoint. Because tracks deactivate at five misses, the value remains 5 after timeout rather than continuing to increase.

| Switch checkpoint | Track change | Old-track `missed_frames` in the 10 immediately preceding frames | Actual timeout run after last observation | Bottle present in sparse GT during gap? | Diagnosis |
| ---: | --- | --- | --- | --- | --- |
| 510 | 0 → 14 | `500:5(I), 501:5(I), 502:5(I), 503:5(I), 504:5(I), 505:5(I), 506:5(I), 507:5(I), 508:5(I), 509:5(I)` | last seen 374; `375:1, 376:2, 377:3, 378:4, 379:5` | Yes: bottle at labeled checkpoints 390, 420, 450, 480, 510 | Detection gap; expected timeout/recreation behavior |
| 960 | 14 → 22 | `950:5(I), 951:5(I), 952:5(I), 953:5(I), 954:5(I), 955:5(I), 956:5(I), 957:5(I), 958:5(I), 959:5(I)` | last seen 748; `749:1, 750:2, 751:3, 752:4, 753:5` | Yes: 750, 780, 810, 840, 870, 900, 930, 960 | Detection gap; expected timeout/recreation behavior |
| 1530 | 22 → 36 | `1520:5(I), 1521:5(I), 1522:5(I), 1523:5(I), 1524:5(I), 1525:5(I), 1526:5(I), 1527:5(I), 1528:5(I), 1529:5(I)` | last seen 1053; `1054:1, 1055:2, 1056:3, 1057:4, 1058:5` | Yes: every labeled bottle checkpoint 1080–1530 | Detection gap; expected timeout/recreation behavior |
| 1560 | 36 → 37 | `1550:5(I), 1551:5(I), 1552:5(I), 1553:5(I), 1554:5(I), 1555:5(I), 1556:5(I), 1557:5(I), 1558:5(I), 1559:5(I)` | last seen 1537; `1538:1, 1539:2, 1540:3, 1541:4, 1542:5` | Yes: 1560 (and preceding checkpoint 1530) | Detection gap; expected timeout/recreation behavior |
| 1680 | 37 → 44 | `1670:5(I), 1671:5(I), 1672:5(I), 1673:5(I), 1674:5(I), 1675:5(I), 1676:5(I), 1677:5(I), 1678:5(I), 1679:5(I)` | last seen 1560; `1561:1, 1562:2, 1563:3, 1564:4, 1565:5` | Yes: 1590, 1620, 1650, 1680 | Detection gap; expected timeout/recreation behavior |
| 1710 | 44 → 45 | `1700:5(I), 1701:5(I), 1702:5(I), 1703:5(I), 1704:5(I), 1705:5(I), 1706:5(I), 1707:5(I), 1708:5(I), 1709:5(I)` | last seen 1686; `1687:1, 1688:2, 1689:3, 1690:4, 1691:5` | Yes: 1710 (and preceding checkpoint 1680) | Detection gap; expected timeout/recreation behavior |
| 1950 | 45 → 62 | `1940:5(I), 1941:5(I), 1942:5(I), 1943:5(I), 1944:5(I), 1945:5(I), 1946:5(I), 1947:5(I), 1948:5(I), 1949:5(I)` | last seen 1714; `1715:1, 1716:2, 1717:3, 1718:4, 1719:5` | Yes: 1740, 1770, 1800, 1830, 1860, 1890, 1920, 1950 | Detection gap; expected timeout/recreation behavior |
| 1980 | 62 → 65 | `1970:5(I), 1971:5(I), 1972:5(I), 1973:5(I), 1974:5(I), 1975:5(I), 1976:5(I), 1977:5(I), 1978:5(I), 1979:5(I)` | last seen 1951; `1952:1, 1953:2, 1954:3, 1955:4, 1956:5` | Yes: 1980 (and preceding checkpoint 1950) | Detection gap; expected timeout/recreation behavior |

All eight old tracks reached the configured five-miss timeout before the replacement track was associated with `bottle_1`. None is a no-gap switch, so this evidence does not indicate a tracker-matching bug. Ground truth is available only every 30 frames; “present” above means present at the listed hand-labeled checkpoints, not a claim about every intervening frame.

## Finding 3 — below-threshold confidence distribution

The 20 correct-class near misses are 40.82% of bottle FNs, so this is a meaningful share. This section reports headroom only; it is not a threshold-change recommendation or a false-positive sweep.

| Statistic | Confidence | Headroom below 0.35 |
| --- | ---: | ---: |
| Minimum | 0.2582 | 0.0918 |
| Q1 | 0.2913 | 0.0587 |
| Median | 0.3167 | 0.0333 |
| Mean | 0.3113 | 0.0387 |
| Q3 | 0.3342 | 0.0158 |
| Maximum | 0.3468 | 0.0032 |

| Frame | Raw `bottle` confidence | Headroom below 0.35 |
| ---: | ---: | ---: |
| 1380 | 0.2582 | 0.0918 |
| 1320 | 0.2677 | 0.0823 |
| 1260 | 0.2705 | 0.0795 |
| 1230 | 0.2841 | 0.0659 |
| 1170 | 0.2875 | 0.0625 |
| 1740 | 0.2926 | 0.0574 |
| 1890 | 0.2933 | 0.0567 |
| 1350 | 0.3111 | 0.0389 |
| 1470 | 0.3154 | 0.0346 |
| 780 | 0.3161 | 0.0339 |
| 1440 | 0.3173 | 0.0327 |
| 930 | 0.3199 | 0.0301 |
| 750 | 0.3218 | 0.0282 |
| 1290 | 0.3272 | 0.0228 |
| 1650 | 0.3333 | 0.0167 |
| 1500 | 0.3367 | 0.0133 |
| 1620 | 0.3385 | 0.0115 |
| 1920 | 0.3419 | 0.0081 |
| 480 | 0.3462 | 0.0038 |
| 1590 | 0.3468 | 0.0032 |

| Hypothetical threshold | These 20 near misses admitted | Share of this near-miss bucket |
| ---: | ---: | ---: |
| 0.34 | 3 | 15% |
| 0.33 | 6 | 30% |
| 0.32 | 8 | 40% |
| 0.30 | 13 | 65% |
| 0.25 | 20 | 100% |

The closest gains are three detections at 0.3419–0.3468, requiring at most 0.0081 threshold headroom. Recovering half or more of this bucket would require moving below roughly the 0.3167 median. These counts say nothing about how many unrelated raw predictions would also pass at each threshold; that requires a separate precision/threshold sweep and is intentionally outside this no-fix phase.
