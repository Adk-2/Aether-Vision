# Phase 4 step 1: labeling helper

Command:

```text
python -m evaluation.label_video --video PATH --every-n-frames N
```

Behavior verified from tests, without running model inference:

- Decodes the supplied video and extracts source frame indices `0, N, 2N, ...`.
- Writes JPEGs and `labels.json` into the sibling `<video-stem>_labels` directory.
- Each frame entry contains its source frame index, timestamp when source FPS is available, JPEG filename, an empty `visible_objects` array, and an empty `events` array.
- The schema documents `tag`, `class`, pixel center, and the allowed event vocabulary. It provides no predicted annotations.
- Refuses to overwrite an existing `labels.json`, protecting hand labels.
- Rejects nonpositive sampling intervals and videos that cannot be opened.
- Raw self-recorded video and extracted JPEG patterns are ignored by Git; hand-edited JSON remains eligible for version control.

Raw verification output:

```text
1 file reformatted, 1 file left unchanged
All checks passed!
.................................................................. [ 69%]
.............................                                            [100%]
95 passed, 6 subtests passed in 11.62s
```

No files existed under `data/evaluation/own_clips/` at this step, so no real or inferred annotation values were created.
