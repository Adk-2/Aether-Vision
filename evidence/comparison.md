# Before/after measurements

Baseline: before.md, captured after both triage commits at 28460be. Final: after.md. All counts/values below are from executed evaluation, not inferred improvements.

Jitter definition changed from frames to (track, frame) pairs. Re-running the legacy zero-threshold policy under the corrected definition gives the same baseline rates: raw 8/8, filtered 1/2. Real moves missed is newly printed; its before values below are explicitly recomputed with the legacy zero-threshold policy and unchanged fixtures.

| Scenario | Metric | Before | After |
| --- | --- | --- | --- |
| Identity Stability | steady-state pooled accuracy | 100.00% (9000/9000 steady-state pooled accuracy) | 100.00% (9000/9000 steady-state pooled accuracy) |
| Identity Stability | steady-state accuracy mean | 100.0000 % | 100.0000 % |
| Identity Stability | cold start mean | 1.3250 frames | 1.3250 frames |
| Identity Stability | steady-state accuracy min | 100.0000 % | 100.0000 % |
| Identity Stability | cold start min | 1 frames | 1 frames |
| Identity Stability | steady-state accuracy max | 100.0000 % | 100.0000 % |
| Identity Stability | cold start max | 4 frames | 4 frames |
| Identity Stability | frames until switch | 31 frames | 31 frames |
| Identity Stability | largest burst neither identity nor belief flips | 20 frames | 20 frames |
| Belief Stability | steady-state pooled accuracy | 99.57% (8961/9000 steady-state pooled accuracy) | 100.00% (9000/9000 steady-state pooled accuracy) |
| Belief Stability | steady-state accuracy mean | 99.5667 % | 100.0000 % |
| Belief Stability | cold start mean | 5.4500 frames | 10.3750 frames |
| Belief Stability | steady-state accuracy min | 97.3333 % | 100.0000 % |
| Belief Stability | cold start min | 1 frames | 10 frames |
| Belief Stability | steady-state accuracy max | 100.0000 % | 100.0000 % |
| Belief Stability | cold start max | 28 frames | 13 frames |
| Belief Stability | frames until switch | 43 frames | 43 frames |
| Belief Stability | largest burst neither identity nor belief flips | 20 frames | 20 frames |
| Event Quality | precision tp/(tp+fp) | 80.95% (34/42 precision tp/(tp+fp)) | 100.00% (34/34 precision tp/(tp+fp)) |
| Event Quality | recall tp/(tp+fn) | 100.00% (34/34 recall tp/(tp+fn)) | 100.00% (34/34 recall tp/(tp+fn)) |
| Event Quality | F1 | 89.47% (tp=34; fp=8; fn=0) | 100.00% (tp=34; fp=0; fn=0) |
| Event Quality | jitter false-movement rate | 100.00% (8/8 jitter false-movement rate) | 0.00% (0/8 jitter false-movement rate) |
| Event Quality | real moves missed | 0 events (legacy-policy recomputation) | 0 events |
| Event Pipeline Quality (engine + filter) | precision tp/(tp+fp) | 87.50% (7/8 precision tp/(tp+fp)) | 100.00% (8/8 precision tp/(tp+fp)) |
| Event Pipeline Quality (engine + filter) | recall tp/(tp+fn) | 87.50% (7/8 recall tp/(tp+fn)) | 100.00% (8/8 recall tp/(tp+fn)) |
| Event Pipeline Quality (engine + filter) | F1 | 87.50% (tp=7; fp=1; fn=1) | 100.00% (tp=8; fp=0; fn=0) |
| Event Pipeline Quality (engine + filter) | jitter false-movement rate | 50.00% (1/2 jitter false-movement rate) | 0.00% (0/2 jitter false-movement rate) |
| Event Pipeline Quality (engine + filter) | real moves missed | 1 events (legacy-policy recomputation) | 0 events |
| Reasoning Regression (golden cases) | cases | 100.00% (9/9 cases) | 100.00% (9/9 cases) |
| Planner Regression (golden cases) | cases | 100.00% (6/6 cases) | 100.00% (6/6 cases) |
| Query Accuracy | CURRENT_OBJECTS supported | 100.00% (6/6 CURRENT_OBJECTS supported) | 100.00% (6/6 CURRENT_OBJECTS supported) |
| Query Accuracy | LAST_SEEN supported | 100.00% (6/6 LAST_SEEN supported) | 100.00% (6/6 LAST_SEEN supported) |
| Query Accuracy | RECENT_HISTORY supported | 100.00% (7/7 RECENT_HISTORY supported) | 100.00% (7/7 RECENT_HISTORY supported) |
| Query Accuracy | VISIBILITY supported | 100.00% (7/7 VISIBILITY supported) | 100.00% (7/7 VISIBILITY supported) |
| Query Accuracy | WHERE_IS supported | 100.00% (8/8 WHERE_IS supported) | 100.00% (8/8 WHERE_IS supported) |
| Query Accuracy | WHERE_WAS supported | 100.00% (6/6 WHERE_WAS supported) | 100.00% (6/6 WHERE_WAS supported) |
| Query Accuracy | supported questions | 100.00% (40/40 supported questions) | 100.00% (40/40 supported questions) |
| Query Accuracy | paraphrases | 0.00% (0/60 paraphrases) | 0.00% (0/60 paraphrases) |
| Query Accuracy | supported confidently wrong answers | 0.00% (0/40 supported confidently wrong answers) | 0.00% (0/40 supported confidently wrong answers) |
| Query Accuracy | paraphrases confidently wrong answers | 0.00% (0/60 paraphrases confidently wrong answers) | 0.00% (0/60 paraphrases confidently wrong answers) |

## Performance measurements

These compare the immediately pre/post world-copy optimization, with identical event and belief policies. Video: data/evaluation/vtest.avi, yolov8n.pt, inference [640, 640], source 768x576. Five warm-up frames excluded. Timing scope excludes decoding, rendering, and persistence. Replay is explicit; detector/system timing varies across runs.

### Original clip: 795 frames, 790 measured

| Stage | Before p50 ms | After p50 ms | Before p95 ms | After p95 ms |
| --- | ---: | ---: | ---: | ---: |
| detector | 36.9406 | 24.6781 | 48.9522 | 32.2323 |
| adapter | 1.8698 | 1.7954 | 3.4081 | 2.9181 |
| confidence filter | 0.0023 | 0.0022 | 0.0042 | 0.0035 |
| tracker | 0.0781 | 0.0584 | 0.1314 | 0.0954 |
| stabilizer | 0.1671 | 0.1617 | 0.2633 | 0.2553 |
| identity | 0.3193 | 0.2808 | 0.6816 | 0.5687 |
| belief | 0.0305 | 0.0289 | 0.0481 | 0.0421 |
| world + apply beliefs | 26.2809 | 0.0783 | 51.2717 | 0.1385 |
| event engine | 0.0615 | 0.0504 | 0.1225 | 0.0746 |
| event filter | 0.0069 | 0.0066 | 0.0230 | 0.0163 |
| memory | 0.0007 | 0.0006 | 0.0098 | 0.0079 |
| timeline | 0.0006 | 0.0005 | 0.0111 | 0.0094 |
| query | 0.1049 | 0.0883 | 0.2018 | 0.1521 |

| Other metric | Before | After |
| --- | --- | --- |
| End-to-end mean FPS | 15.0802 | 35.4004 |
| FPS excluding detector | 31.9543 | 342.2974 |
| first 200: world p50 ms | 11.5073 | 0.0626 |
| first 200: median history entries | 629.0 | 629.0 |
| first 200: median active tracks | 9.0 | 9.0 |
| last 200: world p50 ms | 41.6493 | 0.0959 |
| last 200: median history entries | 2090.0 | 2090.0 |
| last 200: median active tracks | 10.0 | 10.0 |

### Explicit replay: 2000 frames, 1995 measured

| Stage | Before p50 ms | After p50 ms | Before p95 ms | After p95 ms |
| --- | ---: | ---: | ---: | ---: |
| detector | 39.7635 | 27.4550 | 76.8363 | 46.7794 |
| adapter | 1.9444 | 2.0312 | 3.7193 | 3.9102 |
| confidence filter | 0.0024 | 0.0025 | 0.0039 | 0.0045 |
| tracker | 0.1073 | 0.0761 | 0.1745 | 0.1363 |
| stabilizer | 0.1760 | 0.1818 | 0.2759 | 0.3164 |
| identity | 0.5058 | 0.4388 | 0.9660 | 0.9611 |
| belief | 0.0337 | 0.0348 | 0.0521 | 0.0574 |
| world + apply beliefs | 42.9737 | 0.0994 | 83.5749 | 0.1984 |
| event engine | 0.0657 | 0.0570 | 0.1141 | 0.1037 |
| event filter | 0.0080 | 0.0072 | 0.0231 | 0.0186 |
| memory | 0.0007 | 0.0008 | 0.0100 | 0.0095 |
| timeline | 0.0006 | 0.0007 | 0.0112 | 0.0118 |
| query | 0.1741 | 0.1733 | 0.3206 | 0.3343 |

| Other metric | Before | After |
| --- | --- | --- |
| End-to-end mean FPS | 11.2749 | 30.0552 |
| FPS excluding detector | 20.6791 | 274.9140 |
| first 200: world p50 ms | 11.5948 | 0.0670 |
| first 200: median history entries | 629.0 | 629.0 |
| first 200: median active tracks | 9.0 | 9.0 |
| last 200: world p50 ms | 71.3321 | 0.1272 |
| last 200: median history entries | 3018.5 | 3018.5 |
| last 200: median active tracks | 9.0 | 9.0 |

## Interpretation

- Event quality improved without editing event ground truth. The 1-pixel default is tuned on synthetic fixtures; slow subthreshold movement can still be suppressed.
- Belief mean cold-start latency increased (5.45 to 10.375 frames); worst observed startup improved (28 to 13) and all 20-seed steady-state observations are correct. Unpublished beliefs count as incorrect rather than disappearing from the denominator.
- Reasoning and planner are 100% at both ends of this comparison, because authorized oracle corrections preceded baseline capture.
- Paraphrase coverage remains 0/60; none of those answers is confidently wrong because all abstain.
- Snapshot history remains unbounded and list copying remains linear. See world-profile.md and world-fix.md for measured cause and residual limits.
