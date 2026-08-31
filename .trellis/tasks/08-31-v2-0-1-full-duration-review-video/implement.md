# v2.0.1 60-second Office review video — Implementation Plan

## Phase A — Freeze authorization and source

- [x] Recheck branch, HEAD, parent/child task state, staged paths, all relevant
  dirty paths, current ledger, and existing local/remote run IDs.
- [x] Record the actual product-source commit and hashes for the runner, Office
  native driver, bridge package, Foxy workspace inputs, RViz config, thresholds,
  policy identity, and current v2.0.1 build.
- [x] Append `office_v2_0_1_go2_geometry_dryrun01`, the 60-second authorization,
  gates, artifact contract, and non-promotion boundary to the ledger before
  remote execution; validate ledger/tests.

**Gate A:** the run is authorized and registered without changing prior
evidence or scientific inputs.

## Phase B — Pre-run validation

- [x] Run targeted/full local bridge tests, ledger validator, Trellis validator,
  shell syntax, Python compile, JSON parsing and `git diff --check`.
- [x] Live-check compute-helper configuration; if no leased node is available,
  record that boundary and use the already configured `gpu5070ti` SSH execution
  copy only after identity/GPU/display/container checks pass.
- [x] Verify Python, GPU/driver, X display/Xauthority, Foxy image/install,
  ffmpeg/libx264, disk space, remote work roots and two free ports.
- [x] Sync only reviewed runtime inputs and compare local/remote SHA-256. Confirm
  the dry-run ID and driver log do not exist locally or remotely.

**Gate B:** no remote run starts while source identity, environment, port or
local validation is uncertain.

## Phase C — Execute the immutable 60-second run

- [x] Run the native-RViz Office driver with duration `60`, terminal gate `1`,
  pedestrian gate `1`, current `upstream_go2_reference` profile, and selected
  free ports.
- [x] Monitor without interrupting normal slow-wall-clock execution. Preserve
  partial output and driver log on any failure.
- [x] Validate minimum duration, goal, terminal stop, pedestrian motion,
  runtime safety, dual-cloud pairing/continuity, raw-cloud visibility,
  native-RViz audit, combined media and master hash.

**Gate C:** one 60-second run passes every declared full-duration dry-run gate;
otherwise it remains immutable FAIL and receives no promotion.

## Phase D — Create the delivery copy

- [x] Preserve the driver-generated 4K master and standard transfer file.
- [x] Encode a new `office_review_third_person_rviz_4k_transfer_under10mb.mp4`
  at preferred `1920x540`, 25 fps, H.264 High/YUV420p/BT.709 using a conservative
  two-pass target; never overwrite an existing output.
- [x] Validate `<10,000,000` bytes, complete decode, frame/duration parity,
  panel order/aspect, master/standard-transfer hashes unchanged, SSIM against a
  same-resolution reference, and direct contact-sheet/video legibility.
- [x] Record exact ffmpeg commands/version, media probes, hashes, bytes, ratio,
  SSIM, inspection result and claim boundary.

**Gate D:** the directly delivered entity is complete and legible under the
project byte limit; otherwise delivery remains FAIL while the master is kept.

## Phase E — Recover and close out

- [x] Generate a complete remote recursive SHA-256 manifest and recover the
  declared canonical local delivery subset, including all videos needed for
  review and all small audit/provenance files.
- [x] Verify every recovered file against the remote manifest; record remote-only
  raw rosbag/voxel paths and sizes rather than claiming complete local parity.
- [x] Append immutable success/failure measurements and evidence hashes to the
  ledger; update REPORT/CHANGE_CONTROL/experiment index, Trellis and project
  hot/cold memory.
- [x] Re-run local quality gates against recovered evidence, inspect task-owned
  diff, stage only task paths, commit and push the canonical branch.
- [x] Return directly openable local master and sub-10 MB video paths, raw gate
  numbers, hashes, remote/local evidence scope, rollback, and remaining human
  decision.

**Gate E:** canonical local review evidence is hash-backed and the outcome is
reported as a dry run pending Dr Sun, never as automatic AC55/formal acceptance.

## Execution outcome

- `dryrun01` is immutable FAIL after the attached channel closed during
  packaging; the completed simulator and partial evidence were not relabeled.
- The postprocessor bridge-path defect was fixed and regression-tested before
  the detached `dryrun02` retry.
- `dryrun02` passed every declared flat full-duration gate and produced the
  preserved 4K master plus standard transfer.
- The first 1920x540 under-10 MB encode is retained as objective quality FAIL
  (SSIM 0.939357). The new non-overwriting 1280x360 `_under10mb_v2` entity is
  9,176,726 bytes, SSIM 0.964990, and passed automated plus local visual review.
- The complete remote trees have 366-entry (`dryrun01`) and 398-entry
  (`dryrun02`) recursive SHA-256 manifests; only the declared review/audit
  subsets were recovered locally.

## Planned commands

```bash
PYTHONPATH=integration/lite3_sim_bridge python3 -m unittest \
  integration.lite3_sim_bridge.tests.test_protocol \
  integration.lite3_sim_bridge.tests.test_isaac_adapter_core \
  integration.lite3_sim_bridge.tests.test_delivery_reliability \
  integration.lite3_sim_bridge.tests.test_office_review_presentation \
  integration.lite3_sim_bridge.tests.test_office_revision_ledger

PYTHONPATH=integration/lite3_sim_bridge python3 -m unittest discover \
  -s integration/lite3_sim_bridge/tests -p 'test_*.py'

python3 .trellis/scripts/task.py validate \
  08-31-v2-0-1-full-duration-review-video
python3 .pipeline/experiments/2026-08-17_office_l0_scan_crowd/validate_revision_ledger.py \
  --ledger .pipeline/experiments/2026-08-17_office_l0_scan_crowd/revision_ledger.json \
  --repository-root .

SCAN_NATIVE_RVIZ_REQUIRE_TERMINAL_GATE=1 \
SCAN_NATIVE_RVIZ_REQUIRE_PEDESTRIAN_MOTION_GATE=1 \
bash run_remote_office_crowd_native_rviz.sh \
  office_v2_0_1_go2_geometry_dryrun01 60 <telemetry-port> <command-port>
```

## Pre-start review

- [x] Dr Sun selected the 60-second complete-duration option.
- [x] Current v2.0.1 flat Office source and sub-10 MB transfer rule are fixed by
  repository evidence.
- [x] No non-flat, formal-candidate, AC55, training or real-robot action is
  authorized.
- [x] Inline mode remains active; no implementation/check sub-agent is used.
- [x] Dr Sun approves this final PRD/design/implementation summary before
  `task.py start`.
