# Office R2.0.1 Live Cloud and Transfer Reliability — Implementation Plan

## Phase A — Freeze the real baseline and register the revision

- [x] Re-check branch, HEAD, full dirty-path list, current task, parent-task
  status, remote alias/config, and protected run namespaces.
- [x] Record pre-edit SHA-256 for every owned file that may change.
- [x] Make the first non-task edit the append-only ledger migration and planned
  `office-r2.0.1-preflight` entry; update its validator/tests and validate it.
- [x] Confirm parent and Office aggregate tasks remain `in_progress`.

**Gate A:** r2.0.0 is preserved, r2.0.1 is planned before runtime edits, and no
unrelated user path is modified or staged.

## Phase B — Implement persistent display and fail-closed auditing

- [x] Verify RViz PointCloud2 decay-zero semantics from authoritative source
  and the deployed Foxy runtime; record the evidence.
- [x] Change only the `Live LiDAR Cloud` persistence value while retaining
  `/quad_0/cloud`, best-effort sensor QoS, color, size, and the other displays.
- [x] Add a ROS-independent point-cloud continuity audit core with exact stats,
  thresholds, visibility sequencing, and JSON schema.
- [x] Add an observation-only `/quad_0/cloud` subscription in live mode and
  require the live LiDAR gate in the native launch.
- [x] Extend the driver to preserve partial evidence, finalize the same-run
  generated/received/video audit, and fail before PASS packaging on any failed
  check.
- [x] Add behavior tests for all ten required positive/negative cases, including
  semantic display expiration and synthetic video blank sequences.

**Gate B:** targeted tests prove the defect boundary; no code republishes,
duplicates, synthesizes, or substitutes the live cloud.

## Phase C — Implement and validate transfer compression

- [x] Add exclusive output paths for transfer MP4, ffprobe, validation, SHA,
  compression manifest, and CRF comparison evidence.
- [x] Encode CRF 22/24/26 candidates using libx264 slow and the frozen media
  contract; validate full decode, frame/duration/media parity, reduction, SSIM,
  optional VMAF, layout, and detail legibility.
- [x] Select the smallest candidate that passes every gate, preserve the master,
  and make the selected transfer entity the preferred sync artifact.
- [x] Add regression coverage for master preservation, candidate comparison,
  strict media parity, and fail-closed selection.

**Gate C:** transfer output is at least 50% smaller, fully decodable, objectively
measured, visibly legible, and cannot overwrite or impersonate the master.

## Phase D — Local quality gate

- [x] Run targeted continuity, replay-core, presentation, compression, and
  ledger tests.
- [x] Run the full bridge test suite with the project PYTHONPATH.
- [x] Run Trellis task validation and the revision-ledger validator.
- [x] Run shell syntax checks, Python compile checks, JSON/JSONL parsing, and
  `git diff --check`.
- [x] Review the complete owned diff, protected-path status, and test quality;
  verify the old 0.4-second and zero-live-count defects cannot pass.

**Gate D:** every local check passes before any sync or remote run.

## Phase E — 5070 Ti short visual preflight

- [x] Use project `compute-helper` configuration to live-check SSH identity,
  Python, RTX 5070 Ti/driver, display, Foxy image/container, RViz config,
  execution paths, free telemetry/command ports, and run-ID nonexistence.
- [x] Sync only task-owned reviewed files to the execution copies and compare
  local/remote source hashes before running.
- [x] Run approximately 10 seconds with terminal and full-duration pedestrian
  gates disabled, beginning with
  `office_crowd_r2_0_1_live_cloud_transfer_preflight01`.
- [x] Preserve any failed run and its driver log; diagnose, update the ledger if
  source/config changes, and use the next unused suffix.
- [x] Inspect the real native RViz capture and transfer comparison outputs; do
  not promote an automated result without visual evidence.

**Gate E:** one immutable short preflight passes all r2.0.1 automated gates and
remains explicitly pending Dr Sun's visual review.

## Phase F — Recover, archive, commit, and push

- [x] Copy the complete remote result tree into the canonical local results
  path and compare recursive SHA-256 manifests byte-for-byte.
- [x] Re-run local audit/ledger/media validation against recovered evidence.
- [x] Write the r2.0.1 revision Markdown and manifest with before/after file
  hashes, commands, runs, failures, evidence, limitations, rollback, and next
  step.
- [x] Update CHANGE_CONTROL, REPORT, experiment README/index, Trellis records,
  project hot/cold memory, and one global ad-hoc memory update note.
- [x] Re-run the complete local quality gate, review `git diff --check`, and
  stage only task-owned paths.
- [x] Review the staged diff, create one fix commit, record its hash in rollback
  material where possible without creating a second fix commit, and push
  `codex/scan-foxy-isaac`.
- [x] Return the requested raw numbers, hashes, paths, rollback command, claim
  boundary, and directly openable local transfer MP4.

**Gate F:** canonical local evidence, recursive hash parity, complete archives,
one reviewed task-owned fix commit, and canonical-branch push are all proven.

## Validation commands

```bash
PYTHONPATH=integration/lite3_sim_bridge python3 -m unittest \
  integration.lite3_sim_bridge.tests.test_rviz_replay_core \
  integration.lite3_sim_bridge.tests.test_office_review_presentation \
  integration.lite3_sim_bridge.tests.test_office_revision_ledger

PYTHONPATH=integration/lite3_sim_bridge python3 -m unittest discover \
  -s integration/lite3_sim_bridge/tests -p 'test_*.py'

python3 ./.trellis/scripts/task.py validate \
  08-20-office-r2-0-1-live-cloud-transfer
python3 .pipeline/experiments/2026-08-17_office_l0_scan_crowd/validate_revision_ledger.py
bash -n .pipeline/experiments/2026-08-17_office_l0_scan_crowd/run_remote_office_crowd_native_rviz.sh
python3 -m compileall -q integration/lite3_sim_bridge
git diff --check
```

## Risk and rollback points

- The first rollback point is the ledger-only planning entry.
- The second is the local audited implementation before remote sync.
- The third is each immutable remote run before evidence recovery.
- Do not use destructive Git operations. Final rollback is
  `git revert <office-r2.0.1-fix-commit>` and retains every run artifact.

## Pre-start review checklist

- [x] `prd.md`, `design.md`, and `implement.md` agree on scope and thresholds.
- [x] No user-owned product, scope, compatibility, or risk decision remains.
- [x] The task is the child implementation target; parent tasks stay active.
- [x] Inline mode is retained; no implementation/check sub-agent is dispatched.
- [x] Dr Sun explicitly approves this latest planning summary before
  `task.py start`.
