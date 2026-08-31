# v2.0.1 60-second Office review video — Design

## 1. Control boundary

This task adds no new navigation behavior. It authorizes and records one
full-duration flat Office execution of the current
`office-v2.0.1-go2-geometry-preflight` source. The ledger gains a planned dry
run and later an immutable outcome; code/config changes are allowed only if a
pre-run validation defect prevents faithful execution, in which case the
change is reviewed and registered before a new run ID.

## 2. Execution data flow

```text
canonical local committed v2.0.1 source
  -> path-scoped hash-checked sync to 5070 Ti execution copy
  -> 60 s Office L0 / upstream_go2_reference / full gates
  -> raw cloud -> /quad_0/cloud_raw -> native RViz
  -> planner cloud -> /quad_0/cloud -> SCAN
  -> synchronized 4K third-person + native-RViz master
  -> standard validated transfer entity
  -> separately labeled sub-10 MB delivery entity
  -> hash-checked canonical local delivery subset
```

The simulator, bridge, planner, RViz and video processes remain part of one run.
No previously recorded video is extended, looped, concatenated, or presented as
new runtime evidence.

## 3. Full-duration gates

Use the existing native-RViz driver with both duration-dependent gates enabled.
Its declared checks cover:

- minimum simulator duration `>=50 s`;
- goal error `<=0.25 m`;
- continuous `2 s` terminal stop under existing command/speed limits;
- full-duration pedestrian root-motion and animation coherence;
- native-RViz model/path/transform/live-cloud checks;
- dual raw/planner cloud pairing and continuity from the underlying v2.0.1
  bridge evidence;
- 4K combined-video media/trace checks.

This is stronger than the prior 10.04-second presentation preflight but remains
a dry run. Passing these supplemental gates does not itself run or satisfy the
entire formal AC54 evaluator and cannot satisfy AC55.

## 4. Sub-10 MB delivery design

The 60-second 4K master cannot be assumed to remain legible below 10 MB at full
resolution. Preserve it unchanged and create a separately named delivery copy:

- preferred geometry: `1920x540`, preserving the 32:9 dual-panel aspect and
  left/right ordering;
- codec contract: libx264, High, YUV420p, BT.709, 25 fps, no audio;
- deterministic two-pass target chosen with enough container margin to remain
  strictly below 10,000,000 bytes;
- frame count and duration must equal the master within one frame period;
- compare SSIM against a Lanczos-downscaled master reference, not against an
  unmatched 4K raster;
- generate a contact sheet and inspect robot, planned/measured paths, point
  clouds and principal RViz annotations before PASS.

If 1920x540 cannot pass the declared legibility/quality gate below 10 MB, keep
the failed encode and do not claim delivery PASS. The master remains available
locally for high-quality review.

The executed 1920x540 attempt followed this failure path at SSIM 0.939357 and
was preserved. A distinct `_under10mb_v2` 1280x360 encode reused the same
two-pass bitrate budget, passed SSIM 0.964990 and all media/decode checks, and
became the delivered under-10 MB entity without overwriting the failed sample.

## 5. Evidence recovery

The remote result directory remains immutable after the driver exits except for
append-only postprocessing evidence. Generate a sorted recursive remote manifest
before transfer. Recover the human-review videos and all small provenance,
audit, validation, identity and log artifacts to the same canonical local run
path, then verify each selected hash. Raw rosbag/voxel data may remain remote
when its full manifest and exact exclusion scope are recorded; that boundary is
not described as complete local-tree parity.

## 6. Failure and rollback

- Pre-run failure before a result directory exists: preserve the driver log and
  use the same planned ID only if no immutable result/log identity was created;
  otherwise increment the suffix.
- Runtime/gate/compression failure: preserve the complete run and use the next
  suffix after diagnosis; do not edit thresholds to make it pass.
- Ledger/report-only changes can be reverted by the final task commit without
  deleting result directories.
- Any required product-code change returns to the parent v2.0.1 task boundary
  and requires a new reviewed plan before rerun.
